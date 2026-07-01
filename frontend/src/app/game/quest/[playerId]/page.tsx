"use client"

import QuestScreen from "../../../../features/quest/QuestScreen";
import { useParams } from "next/navigation";

export default function QuestPage() {
    const { playerId } = useParams<{ playerId: string }>();
    return (
        <>
            <QuestScreen playerId={playerId} />
        </>
    );
}