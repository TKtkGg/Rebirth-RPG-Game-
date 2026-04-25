import styles from "./StageButton.module.css";
import { StageData } from "@/src/features/stages/types";

type Props = {
    stage: StageData;
    playerLevel: number;
}

export const StageButton = (props: Props) => {
    const { stage, playerLevel } = props;
    const isLocked = stage.unlock_level > (playerLevel);
    return (
        <button
            type="button"
            className={`${styles.stageButton} ${isLocked ? styles.locked : ""}`}
            style={{ backgroundImage: `url("/game/img/背景/${stage.background_image}")` }}
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