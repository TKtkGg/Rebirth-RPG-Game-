"use client"

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";
import { HomeScreenData } from "./types";

type Props = {
    "playerId": string 
}

export default function HomeScreen(props: Props) {
    const { playerId } = props;
    const router = useRouter();
    const [data, setData] = useState<HomeScreenData | null>(null);
    useEffect(() => {
        apiGet(`/api/battle_start/${playerId}/`).then((data: HomeScreenData) => {
            setData(data);
        });
    }, [playerId])
    return (
        <div>
            <h1>ホーム</h1>
            <h1>名前：{data?.name}</h1>
            <h1>ジョブ：{data?.job}</h1>
            <h1>レベル：{data?.level}</h1>
            <h1>経験値：{data?.exp_percent}%</h1>
            <h1>所持金：{data?.gold}</h1>
            <h1>HP：{data?.hp} / {data?.max_hp}</h1>
            <h1>ATK：{data?.atk}</h1>
            <h1>DEF：{data?.defense}</h1>
            <h1>SPD：{data?.spd}</h1>
            <h1>MP：{data?.mp} / {data?.max_mp}</h1>
            
            <button onClick={() => {
                apiPost(`/api/battle_start/${playerId}/`, {
                    action: 'rest',
                }).then((data: HomeScreenData) => {
                    setData(data);
                });
            }}>休む</button>

            <button onClick={() => {
                apiPost(`/api/auth/logout/`, {}).then((data: { ok: boolean }) => {
                    if (data.ok) {
                        localStorage.removeItem('playerId');
                        router.push('/auth/');
                    }
                }).catch((error: { message: string }) => {
                    alert(error.message);
                });
            }}>ログアウト</button>
        </div>
    );
}