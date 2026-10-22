-- ============================================================================
-- Legal Metrology (Packaged Commodities) Rules, 2011 - Compliance Verification
-- Problem Statement ID26034 | Person D - Backend & DB Layer
-- Run this entire script in the Supabase SQL Editor
-- ============================================================================

-- Extensions ------------------------------------------------------------
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ============================================================================
-- Table: scans
-- One row per uploaded label image / scan job
-- ============================================================================
create table if not exists public.scans (
    id              uuid primary key default gen_random_uuid(),
    user_id         uuid null,                       -- references auth.users(id) if using Supabase Auth
    raw_image_url   text not null,                    -- public URL of the uploaded label image (Supabase Storage)
    pdf_report_url  text null,                         -- public URL of the generated compliance PDF report
    status          text not null default 'PENDING',  -- PENDING | PROCESSING | COMPLETED | FAILED
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),

    constraint scans_status_check
        check (status in ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'))
);

comment on table public.scans is 'One row per label scan submitted for Legal Metrology compliance verification';

-- Optional FK to Supabase auth.users. Uncomment if Supabase Auth is enabled
-- and every scan must belong to an authenticated user.
-- alter table public.scans
--     add constraint scans_user_id_fkey
--     foreign key (user_id) references auth.users (id) on delete set null;

create index if not exists idx_scans_user_id on public.scans (user_id);
create index if not exists idx_scans_status on public.scans (status);
create index if not exists idx_scans_created_at on public.scans (created_at desc);

-- ============================================================================
-- Table: extracted_fields
-- OCR / rule-engine extracted mandatory declaration fields for a scan
-- e.g. MRP, Net Quantity, Manufacturer Name, Country of Origin, etc.
-- ============================================================================
create table if not exists public.extracted_fields (
    id            uuid primary key default gen_random_uuid(),
    scan_id       uuid not null,
    field_name    text not null,                -- e.g. 'MRP', 'NET_QUANTITY', 'MFG_DATE'
    field_value   text null,                     -- raw extracted value (null if not found)
    is_present    boolean not null default false,-- whether the field was detected on the label
    created_at    timestamptz not null default now(),

    constraint extracted_fields_scan_id_fkey
        foreign key (scan_id)
        references public.scans (id)
        on delete cascade
);

comment on table public.extracted_fields is 'Mandatory Legal Metrology fields extracted per scan via OCR + rule engine';

create index if not exists idx_extracted_fields_scan_id on public.extracted_fields (scan_id);
create index if not exists idx_extracted_fields_field_name on public.extracted_fields (field_name);

-- ============================================================================
-- Table: violations
-- Rule violations raised by the compliance engine for a given scan
-- ============================================================================
create table if not exists public.violations (
    id            uuid primary key default gen_random_uuid(),
    scan_id       uuid not null,
    rule_code     text not null,       -- e.g. 'LMR_2011_R6_MRP_MISSING'
    description   text not null,
    created_at    timestamptz not null default now(),

    constraint violations_scan_id_fkey
        foreign key (scan_id)
        references public.scans (id)
        on delete cascade
);

comment on table public.violations is 'Non-compliance issues detected for a scan against LMR 2011 rules';

create index if not exists idx_violations_scan_id on public.violations (scan_id);
create index if not exists idx_violations_rule_code on public.violations (rule_code);

-- ============================================================================
-- Trigger: keep scans.updated_at fresh
-- ============================================================================
create or replace function public.set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_scans_updated_at on public.scans;
create trigger trg_scans_updated_at
    before update on public.scans
    for each row
    execute function public.set_updated_at();

-- ============================================================================
-- Row Level Security (adjust policies to your auth model before going to prod)
-- ============================================================================
alter table public.scans enable row level security;
alter table public.extracted_fields enable row level security;
alter table public.violations enable row level security;

-- Service-role key (used by the FastAPI backend) bypasses RLS automatically.
-- The policies below are permissive defaults for development; tighten them
-- once Supabase Auth / JWT-based user scoping is wired up on the frontend.
drop policy if exists "Allow all for authenticated" on public.scans;
create policy "Allow all for authenticated"
    on public.scans for all
    using (true)
    with check (true);

drop policy if exists "Allow all for authenticated" on public.extracted_fields;
create policy "Allow all for authenticated"
    on public.extracted_fields for all
    using (true)
    with check (true);

drop policy if exists "Allow all for authenticated" on public.violations;
create policy "Allow all for authenticated"
    on public.violations for all
    using (true)
    with check (true);

-- ============================================================================
-- Storage: create the bucket used for raw label images (idempotent)
-- ============================================================================
insert into storage.buckets (id, name, public)
values ('raw-labels', 'raw-labels', true)
on conflict (id) do nothing;
