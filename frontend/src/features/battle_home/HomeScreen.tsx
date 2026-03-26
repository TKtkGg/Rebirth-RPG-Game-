"use client"

import { useEffect, useState } from "react";
import { apiGet } from "../../lib/apiClient";

type Props = {
    "playerId": string 
}

export default function HomeScreen(props: Props) {
    const { playerId } = props;
    const [data, setData] = useState<{ name: string, job: string } | null>(null);
    useEffect(() => {
        apiGet(`/api/battle_start/${playerId}/`).then((data: { name: string, job: string }) => {
            setData(data);
        });
    }, [playerId])
    return (
        <div>
            <h1>ホーム</h1>
            <h1>名前：{data?.name}</h1>
            <h1>ジョブ：{data?.job}</h1>
        </div>
    );
}