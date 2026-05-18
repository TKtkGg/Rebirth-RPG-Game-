"use client"

import BattleScreen from "../../../../../../features/battle_battle/BattleScreen";
import { useParams } from "next/navigation";

export default function BattlePage() {
    const { playerId, stageId } = useParams<{ playerId: string, stageId: string }>();
    return (
        <>
            <BattleScreen playerId={playerId} stageId={stageId} />
        </>
    );
}