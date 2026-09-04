"use client";

import React, { useState, useEffect } from "react";
import { Calendar as CalendarIcon, Clock, ExternalLink, AlertCircle, Layers } from "lucide-react";
import { fetchCalendarEvents, fetchActivities } from "@/lib/api";
import { MoodleActivity } from "@/types";
import { ActivityTypeBadge, StatusBadge } from "@/components/ui/ActivityBadge";

export default function CalendarPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [noDeadlineTasks, setNoDeadlineTasks] = useState<MoodleActivity[]>([]);
  const [showBacklog, setShowBacklog] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchCalendarEvents(),
      fetchActivities({ has_deadline: false })
    ])
      .then(([calendarData, noDeadlineData]) => {
        setEvents(calendarData);
        setNoDeadlineTasks(noDeadlineData);
      })
      .catch((err) => console.error("Failed to load calendar data:", err))
      .finally(() => setLoading(false));
  }, []);

  const formatDateGroup = (isoStr: string) => {
    const d = new Date(isoStr);
    return d.toLocaleDateString("en-US", {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  // Group events by Date string
  const groupedEvents: Record<string, any[]> = {};
  events.forEach((ev) => {
    if (ev.due_date) {
      const dayKey = ev.due_date.split("T")[0];
      if (!groupedEvents[dayKey]) groupedEvents[dayKey] = [];
      groupedEvents[dayKey].push(ev);
    }
  });

  const sortedDays = Object.keys(groupedEvents).sort();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Global Assignment Calendar</h1>
          <p className="text-sm text-slate-400 mt-1">
            Strict deadline tracker. Only assignments with confirmed due dates are scheduled here.
          </p>
        </div>

        <button
          onClick={() => setShowBacklog(!showBacklog)}
          className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg border border-slate-800 bg-slate-900 hover:bg-slate-800 text-xs font-medium text-slate-300 transition"
        >
          <Layers className="w-3.5 h-3.5 text-blue-400" />
          <span>{showBacklog ? "Hide No-Deadline Backlog" : `View No-Deadline Items (${noDeadlineTasks.length})`}</span>
        </button>
      </div>

      {showBacklog && (
        <div className="p-5 rounded-xl bg-slate-900/80 border border-blue-500/20 space-y-3">
          <div className="flex items-center space-x-2 text-blue-400 font-semibold text-sm">
            <Layers className="w-4 h-4" />
            <span>No-Deadline Backlog ({noDeadlineTasks.length} items)</span>
          </div>
          <p className="text-xs text-slate-400">
            Per system requirements, activities without strict deadlines remain in their course archives and do not occupy calendar slots.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
            {noDeadlineTasks.map((item) => (
              <div key={item.id} className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <ActivityTypeBadge type={item.activity_type} />
                  <StatusBadge status={item.status} />
                </div>
                <h4 className="font-medium text-white truncate">{item.title}</h4>
                <p className="text-slate-400 text-[11px] truncate">{item.course_name}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {loading ? (
        <div className="py-16 text-center text-slate-400 text-sm">Loading deadlines...</div>
      ) : sortedDays.length === 0 ? (
        <div className="py-16 text-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
          No upcoming deadlines with real due dates found.
        </div>
      ) : (
        <div className="space-y-6">
          {sortedDays.map((day) => (
            <div key={day} className="space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-blue-400 uppercase tracking-wider">
                <CalendarIcon className="w-4 h-4" />
                <span>{formatDateGroup(day)}</span>
              </div>

              <div className="space-y-2.5">
                {groupedEvents[day].map((ev) => (
                  <div
                    key={ev.id}
                    className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition flex items-center justify-between"
                  >
                    <div className="space-y-1 min-w-0 pr-4">
                      <div className="flex items-center space-x-2">
                        <ActivityTypeBadge type={ev.activity_type} />
                        <span className="text-xs text-slate-400 font-medium">{ev.course_name}</span>
                      </div>
                      <h3 className="text-sm font-semibold text-white truncate">{ev.title}</h3>
                    </div>

                    <div className="flex items-center space-x-4 shrink-0 text-right">
                      <div>
                        <div className="text-xs font-bold text-amber-400 flex items-center gap-1 justify-end">
                          <Clock className="w-3 h-3" />
                          <span>
                            {new Date(ev.due_date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        </div>
                        <StatusBadge status={ev.status} />
                      </div>

                      <a
                        href={ev.moodle_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                        title="Open in Moodle"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
