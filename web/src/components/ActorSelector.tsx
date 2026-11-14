import { House, KeyRound, Landmark, Users } from "lucide-react";
import type { ActorProfile, ProfileId } from "../data/types";

const ICON: Record<ProfileId, typeof House> = { OWNER: House, TENANT: KeyRound, COOP: Users, BANK: Landmark };

interface Props {
  profiles: ActorProfile[];
  value: ProfileId;
  onChange: (id: ProfileId) => void;
}

/** "Quién decide": the four actors. Changing it is the demo's main move, so it lives in the verdict band. */
export function ActorSelector({ profiles, value, onChange }: Props) {
  return (
    <div className="actorbar">
      <h2 id="h-actor" className="label">
        Quién decide
      </h2>
      <div className="seg" role="group" aria-labelledby="h-actor">
        {profiles.map((p) => {
          const id = p.profile_id as ProfileId;
          const Icon = ICON[id] ?? Users;
          return (
            <button key={id} type="button" aria-pressed={id === value} data-actor={id} onClick={() => id !== value && onChange(id)}>
              <Icon size={20} strokeWidth={1.5} aria-hidden="true" />
              <span>{p.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
