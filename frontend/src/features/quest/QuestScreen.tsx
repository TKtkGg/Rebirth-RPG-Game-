"use client"

import { apiGet, apiPost } from "@/src/lib/apiClient";
import { useEffect, useState } from "react";
import { QuestScreenData } from "./types";
import { SectionTitle } from "@/src/components/atoms/title/SectionTitle";
import { MainPanel } from "@/src/components/atoms/panel/MainPanel";
import { ReturnButton } from "@/src/components/atoms/button/ReturnButton";
import { useRouter } from "next/navigation";
import styles from "./QuestScreen.module.css";

type Props = {
    playerId: string;
}

export default function QuestScreen(props: Props) {
    const { playerId } = props;
    const [questScreenData, setQuestScreenData] = useState<QuestScreenData | null>(null);
    const [questType, setQuestType] = useState<"life" | "account">("life");
    const router = useRouter();

    useEffect(() => {
        apiGet(`/api/quest/${playerId}`).then((data) => {
            setQuestScreenData(data);
        });
    }, [playerId]);

    const handleClaimQuest = (questId: number) => {
        apiPost(`/api/quest/${playerId}/`, {
            quest_id: questId.toString()
        }).then((data: QuestScreenData) => {
            setQuestScreenData(data);
        });
    };

    const selectedQuests = questType === "life"
        ? questScreenData?.life_quests ?? []
        : questScreenData?.account_quests ?? [];
    const paddedQuests = [...selectedQuests];
    while (paddedQuests.length < 8) {
        paddedQuests.push(null);
    }

    return (
        <div className={styles.screen}>
            <SectionTitle title="クエスト" className={styles.title} />

            <MainPanel state="normal" interactive={false} className={styles.mainBox}>
                <div className={styles.sidebar}>
                    <button
                        type="button"
                        className={`${styles.questTab} ${questType === "life" ? styles.active : ""}`}
                        onClick={() => setQuestType("life")}
                    >
                        ライフ
                    </button>
                    <button
                        type="button"
                        className={`${styles.questTab} ${questType === "account" ? styles.active : ""} ${(questScreenData?.is_guest ?? false) ? styles.disabled : ""}`}
                        disabled={questScreenData?.is_guest ?? false}
                        onClick={() => setQuestType("account")}
                    >
                        アカウント
                    </button>
                </div>

                <div className={styles.content}>
                    <div className={styles.questGrid}>
                        {paddedQuests.map((quest, index) => {
                            if (!quest) {
                                return (
                                    <div key={`empty-${index}`} className={`${styles.questBox} ${styles.empty}`}>
                                        <div className={styles.questTitle}>-</div>
                                        <div className={`${styles.questDescription} ${styles.emptyText}`}>空きスロット</div>
                                    </div>
                                );
                            }

                            const canClaim = quest.is_completed && !quest.is_claimed;
                            return (
                                <button
                                    key={quest.id}
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
                        })}
                    </div>
                </div>
            </MainPanel>

            <ReturnButton className={styles.backButton} onClick={() => router.push(`/game/battle/home/${playerId}`)} />
        </div>
    );
}