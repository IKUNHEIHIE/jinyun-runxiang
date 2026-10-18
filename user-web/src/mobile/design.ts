import designs from "./design-assets.json";
type Screen = keyof typeof designs;
export function designImage(screen: Screen, node: string) {
  return (designs[screen].images as Record<string, string>)[node] || "";
}
export function designIcon(screen: Screen, node: string) {
  return (designs[screen].icons as Record<string, string>)[node] || "";
}
export const categories = [
  { label: "全部", value: "" },
  { label: "泥人张", value: "CLAY_FIGURINE" },
  { label: "风筝", value: "KITE" },
  { label: "年画", value: "NEW_YEAR_PAINTING" },
  { label: "瓷器", value: "CERAMICS" },
  { label: "皮影", value: "SHADOW_PUPPET" },
  { label: "青铜", value: "BRONZE" },
  { label: "刺绣", value: "EMBROIDERY" },
];
export const categoryName = (value: string) =>
  categories.find((c) => c.value === value)?.label || value;
