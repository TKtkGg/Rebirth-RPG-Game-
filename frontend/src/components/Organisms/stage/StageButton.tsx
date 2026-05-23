import styles from "./StageButton.module.css";
import { StageData } from "@/src/features/types/stage_types";
import { useRouter } from "next/navigation";

type Props = {
    stage: StageData;
    playerLevel: number;
    playerId: string;
}

export const StageButton = (props: Props) => {
    const { stage, playerLevel, playerId } = props;
    const isLocked = stage.unlock_level > (playerLevel);
    const router = useRouter();
    return (
        <button
            type="button"
            className={`${styles.stageButton} ${isLocked ? styles.locked : ""}`}
            style={{ backgroundImage: `url("/game/img/背景/${stage.background_image}")` }}
            onClick={() => router.push(`/game/battle/battle/${playerId}/${stage.id}/`)}
            disabled={isLocked}
        >
            {isLocked && (
                <div className={styles.lockedOverlay}>
                    <p className={styles.unlockLabel}>開放条件</p>
                    <p className={styles.unlockText}>レベル{stage.unlock_level}以上</p>
                </div>
            )}
            <p className={styles.stageName}>{stage.name}</p>
        </button>
    );
}