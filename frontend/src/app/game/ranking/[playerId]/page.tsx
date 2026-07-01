"use client"

import RankingScreen from "../../../../features/ranking/RankingScreen";
import { useParams } from "next/navigation";

export default function RankingPage() {
    const { playerId } = useParams<{ playerId: string }>();
    return (
        <>
            <RankingScreen playerId={playerId} />
        </>
    );
}