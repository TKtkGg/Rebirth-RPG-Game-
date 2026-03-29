"use client"

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../lib/apiClient";
import { useRouter } from "next/navigation";

type Props = {
    "playerId": string 
}

export default function HomeScreen(props: Props) {
    const { playerId } = props;
    const router = useRouter();
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