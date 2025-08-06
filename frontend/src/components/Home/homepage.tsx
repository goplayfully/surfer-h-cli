"use client";
import { useState, useEffect } from "react";
import CreateTrajectoryInputArea from "./create-trajectory-input-area";
import { AgentSettings, DEFAULT_SETTINGS, loadSettingsFromStorage, saveSettingsToStorage } from "./settings-sheet";
import SettingsSheet from "./settings-sheet";

const examples = [
  "Find a beef Wellington recipe with a rating of 4.7 or higher and at least 200 reviews.",
  "Search for the latest iPhone price on Amazon",
];

const exampleUrlMappings: Record<string, string> = {
  "Find a beef Wellington recipe with a rating of 4.7 or higher and at least 200 reviews.": "https://www.allrecipes.com",
  "Search for the latest iPhone price on Amazon": "https://www.amazon.com",
};

function ExamplePrompts({ onSelectExample }: { onSelectExample: (example: string) => void }) {
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setVisibleCount((prev) => {
        if (prev < examples.length) {
          return prev + 1;
        }
        clearInterval(timer);
        return prev;
      });
    }, 100); // Reveal one every 100ms

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="w-full max-w-[680px] mt-8 pl-4">
      <div className="space-y-4">
        {examples.slice(0, visibleCount).map((example, index) => (
          <button
            key={index}
            onClick={() => onSelectExample(example)}
            className="w-full text-left text-14-regular-body text-gray-6 hover:text-gray-8 transition-colors duration-200 animate-in fade-in slide-in-from-bottom-1 duration-500 ease-out"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function HomepageContainer() {
  const [message, setMessage] = useState<string>("");
  const [settings, setSettings] = useState<AgentSettings>(DEFAULT_SETTINGS);
  const [isSettingsLoaded, setIsSettingsLoaded] = useState(false);

  // Load settings from localStorage on mount
  useEffect(() => {
    const loadedSettings = loadSettingsFromStorage();
    setSettings(loadedSettings);
    setIsSettingsLoaded(true);
  }, []);

  // Save settings to localStorage whenever they change (but not on initial load)
  useEffect(() => {
    if (isSettingsLoaded) {
      saveSettingsToStorage(settings);
    }
  }, [settings, isSettingsLoaded]);

  const handleSelectExample = (example: string) => {
    setMessage(example);

    // Update the URL in settings if there's a mapping for this example
    const mappedUrl = exampleUrlMappings[example];
    if (mappedUrl) {
      setSettings(prev => ({
        ...prev,
        url: mappedUrl
      }));
    }
  };

  const handleSettingsChange = (newSettings: AgentSettings) => {
    setSettings(newSettings);
  };

  return (
    <div className="relative h-full w-full">
      {/* Settings Button - Top Right */}
      <div className="absolute top-0 right-0 z-10">
        <SettingsSheet
          settings={settings}
          onSettingsChange={handleSettingsChange}
        />
      </div>

      {/* Main Content */}
      <div className="flex flex-col pt-10 md:pt-40 items-center pb-10">
        <div className="flex flex-col md:flex-row items-center text-center mb-4 md:mb-0 md:text-left gap-y-0 md:gap-x-3.5">
          <h1 className="text-36-light-heading">Open SurferH</h1>
        </div>

        <CreateTrajectoryInputArea
          message={message}
          setMessage={setMessage}
          settings={settings}
          setSettings={setSettings}
        />

        <ExamplePrompts onSelectExample={handleSelectExample} />
      </div>
    </div>
  );
}
