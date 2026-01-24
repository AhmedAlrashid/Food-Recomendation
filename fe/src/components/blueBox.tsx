import React from 'react';

interface BlueBoxProps {
    children?: React.ReactNode;
    style?: React.CSSProperties;
}

const BlueBox: React.FC<BlueBoxProps> = ({ children, style }) => (
    <div
        style={{
            backgroundColor: '#2196f3',
            color: '#fff',
            padding: '16px',
            borderRadius: '8px',
            ...style,
        }}
    >
        {children}
    </div>
)

export default BlueBox