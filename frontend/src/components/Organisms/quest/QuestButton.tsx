import styles from "./QuestButton.module.css";
import type { QuestItem } from "@/src/features/quest/types";

type Props = {
    quest: QuestItem | null;
    handleClaimQuest: (questId: number) => void;
}

export default function QuestButton(props: Props) {
    const { quest, handleClaimQuest } = props;

    if (!quest) {
        return (
            <div className={`${styles.questBox} ${styles.empty}`}>
                <div className={styles.questTitle}>-</div>
                <div className={`${styles.questDescription} ${styles.emptyText}`}>空きスロット</div>
            </div>
        );
    }

    const canClaim = quest.is_completed && !quest.is_claimed;

    return (
        <button
            type="button"
            className={`${styles.questBox} ${quest.is_claimed ? styles.claimed : ""} ${canClaim ? styles.completed : ""}`}
            onClick={() => {
                if (canClaim) {
                    handleClaimQuest(quest.id);
                }
            }}
            disabled={quest.is_claimed}
        >
            <div className={styles.questTitle}>{quest.quest_template.title}</div>
            <div className={styles.questDescription}>{quest.quest_template.description}</div>
            <div className={styles.questProgress}>
                {quest.is_claimed
                    ? "報酬受取済"
                    : `${quest.progress_current} / ${quest.quest_template.progress_max}`}
            </div>
            <div className={styles.questReward}>
                EXP +{quest.quest_template.reward_exp}
                <br />
                ゴールド +{quest.quest_template.reward_gold}
            </div>
        </button>
    );
}