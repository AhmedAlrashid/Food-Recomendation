"use client"
import React, { useEffect, useState } from "react"
import { getBackendRoot } from "../../src/api_call/test"
import BlueBox from "../../src/components/blueBox"

export default function Home() {
    const [rootData, setRootData] = useState<any | null>(null)

    useEffect(() => {
        ;(async () => {
            try {
                const data = await getBackendRoot()
                setRootData(data)
            } catch (err) {
                console.error("backend error:", err)
            }
        })()
    }, [])

    return (
        <>
            <p>Hello from /home page</p>
            <BlueBox>
                {rootData ? (
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{JSON.stringify(rootData, null, 2)}</pre>
                ) : (
                    "Loading..."
                )}
            </BlueBox>
        </>
    )
}