import Hero from "@/components/landing/Hero";
import Features from "@/components/landing/Features";
import HowItWork from "@/components/landing/HowItWork";

export default function Home() {
  return (
    <div className="flex flex-col w-full">
      <Hero />
      <Features />
      <HowItWork />
    </div>
  );
}