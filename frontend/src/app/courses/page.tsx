"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { BookOpen, ExternalLink, Archive, CheckCircle2 } from "lucide-react";
import { fetchCourses, updateCourse } from "@/lib/api";
import { Course } from "@/types";

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [activeTab, setActiveTab] = useState<"active" | "archived">("active");
  const [loading, setLoading] = useState(true);

  const loadCourses = async () => {
    try {
      const data = await fetchCourses(false);
      setCourses(data);
    } catch (err) {
      console.error("Failed to load courses:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourses();
  }, []);

  const toggleCourseActive = async (courseId: string, currentActive: boolean) => {
    try {
      await updateCourse(courseId, { is_active: !currentActive });
      loadCourses();
    } catch (err) {
      console.error("Failed to toggle course active status:", err);
    }
  };

  const filteredCourses = courses.filter((c) => (activeTab === "active" ? c.is_active : !c.is_active));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">University Courses</h1>
          <p className="text-sm text-slate-400 mt-1">
            Courses automatically discovered and synchronized from your university Moodle.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1">
          <button
            onClick={() => setActiveTab("active")}
            className={`px-3.5 py-1.5 rounded-md text-xs font-medium transition ${
              activeTab === "active"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Active Courses ({courses.filter((c) => c.is_active).length})
          </button>
          <button
            onClick={() => setActiveTab("archived")}
            className={`px-3.5 py-1.5 rounded-md text-xs font-medium transition ${
              activeTab === "archived"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Archived / Past ({courses.filter((c) => !c.is_active).length})
          </button>
        </div>
      </div>

      {loading ? (
        <div className="py-16 text-center text-slate-400 text-sm">Loading courses...</div>
      ) : filteredCourses.length === 0 ? (
        <div className="py-16 text-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
          {activeTab === "active"
            ? "No active courses found. Click 'Check Moodle Now' to scan Moodle."
            : "No archived courses. Past semester courses will appear here automatically when no longer active."}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredCourses.map((course) => (
            <div
              key={course.id}
              className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {course.short_name || `ID: ${course.moodle_course_id}`}
                  </span>
                  <a
                    href={course.moodle_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-400 hover:text-blue-400 text-xs flex items-center gap-1"
                    title="Open directly in Moodle"
                  >
                    Moodle <ExternalLink className="w-3 h-3" />
                  </a>
                </div>

                <h2 className="text-base font-semibold text-white mt-1 leading-snug">
                  {course.full_name}
                </h2>
                {course.term_or_category && (
                  <p className="text-xs text-slate-400 mt-1">{course.term_or_category}</p>
                )}
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <span>{course.activity_count || 0} tracked activities</span>
                <button
                  onClick={() => toggleCourseActive(course.id, course.is_active)}
                  className="hover:text-slate-200 transition text-[11px] underline"
                >
                  {course.is_active ? "Archive Course" : "Mark Active"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
