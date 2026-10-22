import {
  IndianRupee,
  Scale,
  Building2,
  PhoneCall,
  CalendarClock,
  Globe2,
  Tag,
  type LucideIcon,
} from "lucide-react";

export interface FieldConfigEntry {
  label: string;
  ruleRef: string;
  icon: LucideIcon;
  /** Short helper shown when the field is missing. */
  hint: string;
}

/**
 * Canonical field_name -> display metadata.
 * Covers the 7 fields the current rule engine (services/compliance.py)
 * extracts. Extra entries are included so the grid degrades gracefully
 * if the backend's FIELD_PATTERNS map is extended later (e.g. expiry /
 * best-before dates, importer address) without a frontend redeploy.
 */
export const FIELD_CONFIG: Record<string, FieldConfigEntry> = {
  MRP: {
    label: "MRP (Incl. of all taxes)",
    ruleRef: "Rule 6(1)(f)",
    icon: IndianRupee,
    hint: "Maximum Retail Price is not declared on the package.",
  },
  NET_QUANTITY: {
    label: "Net Quantity",
    ruleRef: "Rule 6(1)(d)",
    icon: Scale,
    hint: "Net quantity in standard units is not declared.",
  },
  MANUFACTURER_NAME: {
    label: "Manufacturer / Packer / Importer",
    ruleRef: "Rule 6(1)(a)",
    icon: Building2,
    hint: "Name and address of manufacturer/packer/importer is missing.",
  },
  CONSUMER_CARE: {
    label: "Consumer Care Details",
    ruleRef: "Rule 6(1)(a)",
    icon: PhoneCall,
    hint: "Consumer care / complaint contact details are missing.",
  },
  MFG_DATE: {
    label: "Month & Year of Manufacture",
    ruleRef: "Rule 6(1)(e)",
    icon: CalendarClock,
    hint: "Date of manufacture / pre-packing is not declared.",
  },
  COUNTRY_OF_ORIGIN: {
    label: "Country of Origin",
    ruleRef: "Rule 6(1) (imports)",
    icon: Globe2,
    hint: "Country of origin is not declared (mandatory for imports).",
  },
  COMMON_NAME: {
    label: "Common / Generic Name",
    ruleRef: "Rule 6(1)(b)",
    icon: Tag,
    hint: "Common or generic name of the commodity is missing.",
  },
  // Forward-compatible entries, not yet emitted by services/compliance.py
  EXPIRY_DATE: {
    label: "Expiry Date",
    ruleRef: "Rule 6(1)(e)",
    icon: CalendarClock,
    hint: "Expiry date is not declared.",
  },
  BEST_BEFORE_DATE: {
    label: "Best Before Date",
    ruleRef: "Rule 6(1)(e)",
    icon: CalendarClock,
    hint: "Best-before date is not declared.",
  },
};

export function getFieldConfig(fieldName: string): FieldConfigEntry {
  return (
    FIELD_CONFIG[fieldName] ?? {
      label: fieldName
        .toLowerCase()
        .split("_")
        .map((w) => w[0]?.toUpperCase() + w.slice(1))
        .join(" "),
      ruleRef: "LMR 2011",
      icon: Tag,
      hint: "This declaration is not present on the label.",
    }
  );
}
