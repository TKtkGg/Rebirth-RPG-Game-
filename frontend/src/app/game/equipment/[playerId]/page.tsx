"use client"

import EquipmentScreen from "../../../../features/equipment/EquipmentScreen";
import { useParams } from "next/navigation";

export default function EquipmentPage() {
    const { playerId } = useParams<{ playerId: string }>();
    return (
        <>
            <EquipmentScreen playerId={playerId} />
        </>
    );
}