"use client";

import { useState } from "react";
import { FaHeart, FaHeartBroken, FaStar } from "react-icons/fa";
import image1 from "./hestu-dancing-with-koroks-in-tears-of-the-kingdom.avif";
import image2 from "./IMG_9518.avif";
import image3 from "./test3.jpg";

const cards = [
    {
        id: 1,
        name: "McDonalds",
        description: "Reviews for McDonalds lol",
        photoRef: image1,
        rating: 4.3,
        location: "Irvine, CA",
        cuisine: "Burger"
    },
    {
        id: 2,
        name: "Wendyyyss",
        description: "Reviews for Wendys lol.",
        photoRef: image2,
        rating: 4.1,
        location: "somewhere, CA",
        cuisine: "Burger"
    },
    {
        id: 3,
        name: "Chipotle",
        description: "Reviews for Chipotle lol.",
        photoRef: image3,
        rating: 4.7,
        cuisine: "Bowls"
    },
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

                        <img src={nextCard.photoRef.src} style={imageStyle} />

                        <div style={contentStyle}>

                            <h2 style={titleStyle}>{nextCard.name}</h2>

                            <div style={ratingStyle}>
                                <span>
                                    {nextCard.location ?? "Unknown"} • {nextCard.rating.toFixed(1)} • {nextCard.cuisine ?? ""}
                                </span>
                                <FaStar size={16} color="#f5c518" />
                            </div>

                            <p style={descriptionStyle}>
                                {nextCard.description}
                            </p>
                            
                        </div>

                    </div>
                )}

                <div
                    style={{
                        ...cardStyle,
                        ...(direction === "left" ? swipeLeft : {}),
                        ...(direction === "right" ? swipeRight : {}),
                    }}
                >

                    <button
                        onClick={() => handleSwipe("left")}
                        style={leftButtonStyle}
                    >
                        <FaHeartBroken size={22} />
                    </button>


                    <button
                        onClick={() => handleSwipe("right")}
                        style={rightButtonStyle}
                    >
                        <FaHeart size={22} />
                    </button>


                    <img src={currentCard.photoRef.src} style={imageStyle} />

                    <div style={contentStyle}>

                        <h2 style={titleStyle}>{currentCard.name}</h2>

                        <div style={ratingStyle}>
                            <span>
                                {currentCard.location ?? "Unknown"} • {currentCard.rating.toFixed(1)}
                            </span>
                            <FaStar size={16} color="#f5c518" />
                            <span>
                                • {currentCard.cuisine ?? ""}
                            </span>
                        </div>

                        <p style={descriptionStyle}>
                            {currentCard.description}
                        </p>

                    </div>

                </div>
            </div>
        </div>
    );
}




// `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference=${currentCard.photoRef}&key=API_KEY` link example

const containerStyle: React.CSSProperties = {
    height: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "#f5f5f5",
};

const stackStyle: React.CSSProperties = {
    position: "relative",
    width: "1000px",
    height: "600px",
};

const cardStyle: React.CSSProperties = {
    position: "absolute",
    width: "100%",
    height: "100%",
    background: "white",
    borderRadius: "20px",
    boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    transition: "transform 0.3s ease, opacity 0.3s ease",
};

const imageStyle: React.CSSProperties = {
    width: "100%",
    height: "65%",
    objectFit: "cover",
};

const contentStyle: React.CSSProperties = {
    padding: "24px",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
};

const titleStyle: React.CSSProperties = {
    margin: 0,
    fontSize: "22px",
    fontWeight: 600,
};

const descriptionStyle: React.CSSProperties = {
    margin: 0,
    fontSize: "15px",
    color: "#555",
    lineHeight: 1.6,
};

const nextCardStyle: React.CSSProperties = {
    transform: "scale(0.95) translateY(25px)",
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

const baseButtonStyle: React.CSSProperties = {
    position: "absolute",
    top: "45%",
    transform: "translateY(-50%)",
    zIndex: 10,
    border: "none",
    borderRadius: "50%",
    width: "60px",
    height: "60px",
    cursor: "pointer",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    boxShadow: "0 4px 10px rgba(0,0,0,0.2)",
};

const leftButtonStyle: React.CSSProperties = {
    ...baseButtonStyle,
    left: "20px",
    background: "rgba(220, 53, 69, 0.9)",
    color: "white",
};

const rightButtonStyle: React.CSSProperties = {
    ...baseButtonStyle,
    right: "20px",
    background: "rgba(40, 167, 69, 0.9)",
    color: "white",
};

const ratingStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "16px",
    fontWeight: 500,
    color: "#333",
};