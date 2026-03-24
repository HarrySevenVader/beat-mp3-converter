import Header from "@/components/Header";

export default function Home() {
  return (
    <main
      style={{
        flex: "1",
        display: "flex",
        justifyContent: "center",
        padding: "32px 16px",
      }}
    >
      <Header />
      <div
        style={{
          width: "100%",
          maxWidth: "960px",
        }}
      />
    </main>
  );
}
