"use client"
import { useEffect, useState } from "react";
import { apiGet } from "../../lib/apiClient";
import { StagesScreenData } from "./types";
import { useRouter } from "next/navigation";

export default function StagesScreen() {
    const [data, setData] = useState<StagesScreenData | null>(null);
    const router = useRouter();
    useEffect(() => {
        apiGet("/api/stages/").then((data: StagesScreenData) => {
            setData(data);
        });
    }, []);
    return(
        <div>
            <h1>ステージ一覧</h1>
            {data?.stages.map((stage) => (
                <div key={stage.id}>
                    <h2>{stage.name}</h2>
                    <p>開放レベル: {stage.unlock_level}</p>
                    <p>背景画像: {stage.background_image}</p>
                    <p>最小敵レベル: {stage.min_enemy_level}</p>
                    <p>最大敵レベル: {stage.max_enemy_level}</p>
                </div>
            ))}
        </div>
    )
}