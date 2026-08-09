export const metadata = { title: "Humanity Tech Tree" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: "#0b0e14", color: "#dbe4f0",
                     fontFamily: "system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
