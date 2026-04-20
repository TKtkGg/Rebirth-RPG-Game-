"use client"

import { apiGet, apiPost } from "@/src/lib/apiClient";
import { useEffect, useState } from "react";
import { QuestScreenData } from "./types";

type Props = {
    playerId: string;
}

export default function QuestScreen(props: Props) {
    const { playerId } = props;
    const [questScreenData, setQuestScreenData] = useState<QuestScreenData | null>(null);
    const [questType, setQuestType] = useState<"life" | "account">("life");

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
    }
    return (
        <div>
            <button onClick={() => setQuestType("life")}>
                ライフ
            </button>
            <button onClick={() => setQuestType("account")} disabled={questScreenData?.is_guest ?? false}>
                アカウント
            </button>
            {questType === "life" && (
                <div>
                    {questScreenData?.life_quests.map((quest, index) => {
                        return (
                            <button 
                                key={quest?.id ?? index}
                                onClick={() => {
                                    if (!!quest && quest?.is_completed && !quest?.is_claimed) {
                                        handleClaimQuest(quest?.id)
                                    }
                                }}
                                disabled={quest === null || quest?.is_completed || quest?.is_claimed}
                            >
                                {quest?.quest_template?.title}
                                {quest?.quest_template?.description}
                                {quest?.quest_template?.condition_target}
                                {quest?.progress_current} / {quest?.quest_template?.progress_max}
                                EXP +{quest?.quest_template?.reward_exp}
                                Gold +{quest?.quest_template?.reward_gold}
                            </button>
                        )
                    })}
                </div>
            )}
            {questType === "account" && (
                <div>
                    {questScreenData?.account_quests.map((quest, index) => {
                        return (
                            <button 
                                key={quest?.id ?? index}
                                onClick={() => {
                                    if (!!quest && quest?.is_completed && !quest?.is_claimed) {
                                        handleClaimQuest(quest?.id)
                                    }
                                }}
                                disabled={quest === null || quest?.is_completed || quest?.is_claimed}
                            >
                                {quest?.quest_template?.title}
                                {quest?.quest_template?.description}
                                {quest?.quest_template?.condition_target}
                                {quest?.progress_current} / {quest?.quest_template?.progress_max}
                                EXP +{quest?.quest_template?.reward_exp}
                                Gold +{quest?.quest_template?.reward_gold}
                            </button>
                        )
                    })}
                </div>
            )}
        </div>
    );
}