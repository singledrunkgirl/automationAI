import { Button } from "@/components/ui/button";
import { TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { Paperclip } from "lucide-react";

interface AttachmentButtonProps {
  onAttachClick: () => void;
  disabled?: boolean;
}

export const AttachmentButton = ({
  onAttachClick,
  disabled = false,
}: AttachmentButtonProps) => {
  return (
    <TooltipPrimitive.Root>
      <TooltipTrigger asChild>
        <Button
          type="button"
          onClick={onAttachClick}
          variant="ghost"
          size="sm"
          className="rounded-full p-0 w-8 h-8 min-w-0"
          aria-label="Attach files"
          data-testid="attach-files-button"
          disabled={disabled}
        >
          <Paperclip className="w-[15px] h-[15px]" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>Add files</p>
      </TooltipContent>
    </TooltipPrimitive.Root>
  );
};
