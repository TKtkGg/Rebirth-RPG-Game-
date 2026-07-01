"use client"

import InventoryScreen from "../../../../features/inventory/InventoryScreen";
import { useParams } from "next/navigation";

export default function InventoryPage() {
    const { playerId } = useParams<{ playerId: string }>();
    return (
        <>
            <InventoryScreen playerId={playerId} />
        </>
    );
}