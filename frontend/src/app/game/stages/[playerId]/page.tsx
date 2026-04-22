"use client"

import StagesScreen from "../../../../features/stages/StagesScreen";
import { useParams } from "next/navigation";

export default function StagesPage() {
    const { playerId } = useParams<{ playerId: string }>();
    return (
        <>
            <StagesScreen playerId={playerId} />
        </>
    );
}