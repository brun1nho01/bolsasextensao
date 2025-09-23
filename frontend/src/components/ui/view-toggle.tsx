import { Button } from "@/components/ui/button";
import { List, LayoutGrid } from "lucide-react";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

interface ViewToggleProps {
  view: "grid" | "list";
  onViewChange: (view: "grid" | "list") => void;
}

export function ViewToggle({ view, onViewChange }: ViewToggleProps) {
  return (
    <ToggleGroup
      type="single"
      value={view}
      onValueChange={(value: "grid" | "list") => {
        if (value) onViewChange(value);
      }}
      className="glass p-1 rounded-lg"
    >
      <ToggleGroupItem
        value="grid"
        aria-label="Toggle grid"
        className="data-[state=on]:bg-primary/20 data-[state=on]:text-primary"
      >
        <LayoutGrid className="h-4 w-4" />
      </ToggleGroupItem>
      <ToggleGroupItem
        value="list"
        aria-label="Toggle list"
        className="data-[state=on]:bg-primary/20 data-[state=on]:text-primary"
      >
        <List className="h-4 w-4" />
      </ToggleGroupItem>
    </ToggleGroup>
  );
}
