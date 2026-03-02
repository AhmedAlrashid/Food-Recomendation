"use client";

import { useState } from "react";
import image1 from "./hestu-dancing-with-koroks-in-tears-of-the-kingdom.avif";
import image2 from "./IMG_9518.avif";
import image3 from "./test3.jpg";

const cards = [ //test cards
    { id: 1, name: "McDonalds", photoRef: image1 },
    { id: 2, name: "Wendyyyss", photoRef: image2 },
    { id: 3, name: "Chipotle", photoRef: image3 },
];

export default function SwipePage() {
    const [index, setIndex] = useState(0);
    const [direction, setDirection] = useState<"left" | "right" | null>(null);
    const [isAnimating, setIsAnimating] = useState(false);

    const handleSwipe = (dir: "left" | "right") => {
        if (index >= cards.length - 1 || isAnimating) return;

        setIsAnimating(true);
        setDirection(dir);

        setTimeout(() => {
            setIndex((prev) => prev + 1);
            setDirection(null);
            setIsAnimating(false);
        }, 300);
    };

    const currentCard = cards[index];
    const nextCard = cards[index + 1];

    return (
        <div style={containerStyle}>
            <div style={stackStyle}>
                {nextCard && (
                    <div style={{ ...cardStyle, ...nextCardStyle }}>
                        <h2>{nextCard.name}</h2>
                        <img
                            src={nextCard.photoRef.src}
                            style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: "20px" }}
                        />
                    </div>
                )}

                <div
                    style={{
                    ...cardStyle,
                    ...(direction === "left" ? swipeLeft : {}),
                    ...(direction === "right" ? swipeRight : {}),
                    }}
                >
                    <h2>{currentCard.name}</h2>
                        <img
                            src={currentCard.photoRef.src}
                            style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: "20px" }}
                        />
                </div>
            </div>

            <div style={{ display: "flex", gap: "20px" }}>
                <button onClick={() => handleSwipe("left")}>Swipe Left</button>
                <button onClick={() => handleSwipe("right")}>Swipe Right</button>
            </div>
        </div>
    );
}

// `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference=${currentCard.photoRef}&key=API_KEY` link example

const containerStyle: React.CSSProperties = {
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    gap: "30px",
};

const stackStyle: React.CSSProperties = {
    position: "relative",
    width: "800px",
    height: "400px",
};

const cardStyle: React.CSSProperties = {
    position: "absolute",
    width: "100%",
    height: "100%",
    background: "white",
    borderRadius: "20px",
    boxShadow: "0 10px 25px rgba(0,0,0,0.15)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    transition: "transform 0.3s ease, opacity 0.3s ease",
};

const nextCardStyle: React.CSSProperties = {
    transform: "scale(0.95) translateY(20px)",
    opacity: 0.8,
};

const swipeLeft: React.CSSProperties = {
    transform: "translateX(-500px) rotate(-20deg)",
    opacity: 0,
};

const swipeRight: React.CSSProperties = {
    transform: "translateX(500px) rotate(20deg)",
    opacity: 0,
};