"use client";

import { useState, useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";

// Define a specific type for our graph events to satisfy TypeScript
interface GraphEvent {
  [key: string]: any; // Allows any string as a key, which is what LangGraph sends
}

export default function Home() {
  const [indicator, setIndicator] = useState("8.8.4.4");
  const [logs, setLogs] = useState(
    "[2023-10-27 10:00:04] CMD: User 'admin' executed 'cat /etc/passwd'."
  );
  
  // Use our new, specific type for the state variables
  const [events, setEvents] = useState<GraphEvent[]>([]);
  const [finalState, setFinalState] = useState<GraphEvent | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    const socket = io(process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000");
    socketRef.current = socket;

    socket.on("connect", () => console.log("Connected to WebSocket server."));
    socket.on("investigation_started", () => {
      setIsStreaming(true);
      setEvents([]);
      setFinalState(null);
    });
    socket.on("graph_event", (event: GraphEvent) => {
      setEvents((prevEvents) => [...prevEvents, event]);
      if (event.__end__) {
        setFinalState(event.__end__);
      }
    });
    socket.on("graph_finished", () => setIsStreaming(false));
    socket.on("graph_error", (data) => {
      console.error("Graph error:", data.error);
      setIsStreaming(false);
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const handleStartInvestigation = () => {
    if (socketRef.current?.connected) {
      socketRef.current.emit("investigate", { indicator, logs });
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-12 bg-gray-900 text-gray-200 font-sans">
      {/* The JSX for the UI remains exactly the same as before */}
      <div className="w-full max-w-4xl">
        <h1 className="text-4xl font-bold text-center mb-2 text-cyan-400">
          Project Cypher
        </h1>
        <p className="text-center text-gray-400 mb-8">
          An Autonomous AI-Powered Security Operations Center
        </p>
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg mb-8">
          <h2 className="text-2xl font-semibold mb-4 text-white">
            Submit a New Alert
          </h2>
          <div className="flex flex-col gap-4">
            <input
              type="text" value={indicator}
              onChange={(e) => setIndicator(e.target.value)}
              placeholder="Enter Indicator (e.g., IP, URL, Hash)"
              className="p-3 bg-gray-700 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
            <textarea
              value={logs} onChange={(e) => setLogs(e.target.value)}
              placeholder="Paste relevant logs here..." rows={4}
              className="p-3 bg-gray-700 rounded-md border border-gray-600 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
            <button
              onClick={handleStartInvestigation}
              disabled={isStreaming}
              className="bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-3 px-6 rounded-md transition duration-300 disabled:bg-gray-500"
            >
              {isStreaming ? "Investigating..." : "Start Investigation"}
            </button>
          </div>
        </div>
        {(events.length > 0 || isStreaming) && (
          <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
            <h2 className="text-2xl font-semibold mb-4 text-white">
              Investigation Details
            </h2>
            <div className="h-64 overflow-y-auto bg-gray-900 p-4 rounded-md font-mono text-sm mb-4">
              {events.filter(e => !e.__end__).map((event, index) => {
                 const nodeName = Object.keys(event)[0];
                 const nodeOutput = event[nodeName];
                 return (
                  <div key={index} className="whitespace-pre-wrap mb-2 border-b border-gray-700 pb-2">
                    <span className="text-green-400">{`> Step ${index + 1}: Running node '${nodeName}'...`}</span>
                    <span className="text-gray-300 block">{JSON.stringify(nodeOutput, null, 2)}</span>
                  </div>
                 )
              })}
              {isStreaming && <div className="text-yellow-400">Awaiting next step...</div>}
            </div>
            {finalState && (
              <>
                <h3 className="text-xl font-semibold mb-2 text-white">Final Report</h3>
                <pre className="bg-gray-900 p-4 rounded-md overflow-x-auto text-sm">
                  {JSON.stringify(finalState, null, 2)}
                </pre>
              </>
            )}
          </div>
        )}
      </div>
    </main>
  );
}