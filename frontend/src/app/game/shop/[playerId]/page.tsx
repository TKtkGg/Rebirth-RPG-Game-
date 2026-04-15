"use client"

import ShopScreen from "../../../../features/shop/ShopScreen";
import { useParams } from "next/navigation";

export default function ShopPage() {
    const { playerId } = useParams<{ playerId: string }>();
    return (
        <>
            <ShopScreen playerId={playerId} />
        </>
    );
}