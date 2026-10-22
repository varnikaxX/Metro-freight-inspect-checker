// Local-only development bypass. Real auth remains the default outside next dev.
// Set NEXT_PUBLIC_DEMO_MODE=false to exercise the real login flow locally.
export const DEMO_MODE =
  process.env.NODE_ENV === "development" &&
  process.env.NEXT_PUBLIC_DEMO_MODE !== "false";

export const DEMO_OFFICER = {
  badgeId: "DEMO-1001",
  name: "Local Demo Officer",
  jurisdiction: "Demo Local Access",
};
