"use client"

import { useRouter } from "next/navigation";

export default function AuthPage() {
    const router = useRouter();
    return (
        <div>
            <button onClick={() => {
                router.push('/auth/login/');
            }}>ログイン</button>
            <button onClick={() => {
                router.push('/auth/signup/');
            }}>サインアップ</button>
        </div>
    )
}