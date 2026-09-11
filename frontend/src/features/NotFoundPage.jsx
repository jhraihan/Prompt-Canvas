import { useNavigate } from "react-router-dom";

import { EmptyState } from "../components/ui/EmptyState";
import { Button } from "../components/ui/Button";
import { InfoIcon, SparkIcon } from "../components/ui/Icons";

export function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <div className="rounded-xl border border-line bg-surface">
      <EmptyState
        icon={<InfoIcon size={20} />}
        title="That page does not exist"
        description="The link may be out of date. Everything you generate is still in your history."
        action={
          <Button variant="primary" onClick={() => navigate("/")} icon={<SparkIcon size={16} />}>
            Go to the generator
          </Button>
        }
      />
    </div>
  );
}
