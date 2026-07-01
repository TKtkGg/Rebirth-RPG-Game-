"use client"

import HomeScreen from "../../../../../features/battle_home/HomeScreen";
import { useParams } from "next/navigation";

export default function HomePage() {
    const { playerId } = useParams<{ playerId: string }>();
    return (
        <>
            <HomeScreen playerId={playerId} />
        </>
    );
}