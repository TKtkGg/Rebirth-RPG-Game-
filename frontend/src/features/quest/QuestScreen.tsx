"use client"

import { apiGet, apiPost } from "@/src/lib/apiClient";
import { useEffect, useState } from "react";
import { QuestScreenData } from "./types";
import { SectionTitle } from "@/src/components/atoms/title/SectionTitle";
import { MainPanel } from "@/src/components/atoms/panel/MainPanel";
import { ReturnButton } from "@/src/components/atoms/button/ReturnButton";
import { useRouter } from "next/navigation";
import styles from "./QuestScreen.module.css";
import SideTabs from "@/src/components/Organisms/quest/SideTabs";
import QuestButton from "@/src/components/Organisms/quest/QuestButton";

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
                <SideTabs questType={questType} setQuestType={setQuestType} isGuest={questScreenData?.is_guest ?? false} />

                <div className={styles.content}>
                    <div className={styles.questGrid}>
                        {paddedQuests.map((quest, index) => {
                            return <QuestButton key={quest ? quest.id : `empty-${index}`} quest={quest} handleClaimQuest={handleClaimQuest} />
                        })}
                    </div>
                </div>
            </MainPanel>

            <ReturnButton className={styles.backButton} onClick={() => router.push(`/game/battle/home/${playerId}`)} />
        </div>
    );
}