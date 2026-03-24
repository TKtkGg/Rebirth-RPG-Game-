"use client"

import { apiGet } from "../lib/apiClient";
import { useEffect } from "react";

export default function Home() {
  useEffect(() => {
    apiGet('/api/start/').then((data: string) => {
      console.log(data);
    })
  }, []);
  return (
    <>
    </>
  );
}
