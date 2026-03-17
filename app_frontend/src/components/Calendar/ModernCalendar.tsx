
// src/components/Calendar/ModernCalendar.tsx
// לוח שנה מודרני בעיצוב Forewise - נקי, מעוגל, ירוק-לבן
import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, Clock, Calendar as CalendarIcon } from 'lucide-react';

// Types
interface CalendarEvent {
  id: string;
  date: Date;
  title: string;
  type: 'worklog' | 'work_order' | 'meeting' | 'deadline';
  status?: 'pending' | 'approved' | 'completed';
}

interface ModernCalendarProps {
  events?: CalendarEvent[];
  onDateSelect?: (date: Date) => void;
  onEventClick?: (event: CalendarEvent) => void;
}

// Hebrew day names
const hebrewDays = ['א׳', 'ב׳', 'ג׳', 'ד׳', 'ה׳', 'ו׳', 'ש׳'];

// Hebrew month names
const hebrewMonths = [
  'ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
  'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'
];

// Event type colors
const eventTypeColors = {
  worklog: 'bg-blue-500',
  work_order: 'bg-kkl-green',
  meeting: 'bg-purple-500',
  deadline: 'bg-red-500',
};

const eventTypeLabels = {
  worklog: 'דיווח שעות',
  work_order: 'הזמנת עבודה',
  meeting: 'פגישה',
  deadline: 'דדליין',
};

const ModernCalendar: React.FC<ModernCalendarProps> = ({
  events = [],
  onDateSelect,
  onEventClick,
}) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());

  // Get calendar data
  const calendarData = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDay = firstDay.getDay();
    const daysInMonth = lastDay.getDate();
    
    const today = new Date();
    const days: Array<{
      date: number;
      fullDate: Date;
      isToday: boolean;
      isCurrentMonth: boolean;
      isSelected: boolean;
      events: CalendarEvent[];
    }> = [];

    // Previous month days
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    for (let i = startDay - 1; i >= 0; i--) {
      const date = prevMonthLastDay - i;
      const fullDate = new Date(year, month - 1, date);
      days.push({
        date,
        fullDate,
        isToday: false,
        isCurrentMonth: false,
        isSelected: false,
        events: [],
      });
    }

    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
      const fullDate = new Date(year, month, i);
      const isToday = 
        today.getDate() === i && 
        today.getMonth() === month && 
        today.getFullYear() === year;
      
      const isSelected = selectedDate && 
        selectedDate.getDate() === i && 
        selectedDate.getMonth() === month && 
        selectedDate.getFullYear() === year;

      // Find events for this day
      const dayEvents = events.filter(event => {
        const eventDate = new Date(event.date);
        return eventDate.getDate() === i && 
               eventDate.getMonth() === month && 
               eventDate.getFullYear() === year;
      });

      days.push({
        date: i,
        fullDate,
        isToday,
        isCurrentMonth: true,
        isSelected: isSelected || false,
        events: dayEvents,
      });
    }

    // Next month days
    const remainingDays = 42 - days.length;
    for (let i = 1; i <= remainingDays; i++) {
      const fullDate = new Date(year, month + 1, i);
      days.push({
        date: i,
        fullDate,
        isToday: false,
        isCurrentMonth: false,
        isSelected: false,
        events: [],
      });
    }

    return days;
  }, [currentDate, selectedDate, events]);

  // Selected day events
  const selectedDayEvents = useMemo(() => {
    if (!selectedDate) return [];
    return events.filter(event => {
      const eventDate = new Date(event.date);
      return eventDate.getDate() === selectedDate.getDate() && 
             eventDate.getMonth() === selectedDate.getMonth() && 
             eventDate.getFullYear() === selectedDate.getFullYear();
    });
  }, [selectedDate, events]);

  // Navigation
  const goToPreviousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const goToToday = () => {
    const today = new Date();
    setCurrentDate(today);
    setSelectedDate(today);
    onDateSelect?.(today);
  };

  // Handle date click
  const handleDateClick = (day: typeof calendarData[0]) => {
    if (!day.isCurrentMonth) return;
    setSelectedDate(day.fullDate);
    onDateSelect?.(day.fullDate);
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-kkl-green to-kkl-green-dark p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CalendarIcon className="w-6 h-6 text-white" />
            <div>
              <h2 className="text-xl font-bold text-white">
                {hebrewMonths[currentDate.getMonth()]} {currentDate.getFullYear()}
              </h2>
              <p className="text-white/70 text-sm">יומן פעילות</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button 
              onClick={goToPreviousMonth}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <ChevronRight className="w-5 h-5 text-white" />
            </button>
            <button 
              onClick={goToToday}
              className="px-4 py-1.5 bg-white/20 hover:bg-white/30 text-white text-sm rounded-lg transition-colors font-medium"
            >
              היום
            </button>
            <button 
              onClick={goToNextMonth}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="p-4">
        {/* Day Headers */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {hebrewDays.map((day, index) => (
            <div 
              key={index} 
              className={`text-center py-2 text-sm font-semibold ${
                index === 6 ? 'text-red-400' : 'text-gray-500'
              }`}
            >
              {day}
            </div>
          ))}
        </div>

        {/* Days Grid */}
        <div className="grid grid-cols-7 gap-1">
          {calendarData.map((day, index) => (
            <button
              key={index}
              onClick={() => handleDateClick(day)}
              disabled={!day.isCurrentMonth}
              className={`
                relative aspect-square p-1 rounded-xl transition-all duration-200
                ${day.isCurrentMonth 
                  ? 'hover:bg-kkl-green-light cursor-pointer' 
                  : 'cursor-default'
                }
                ${day.isToday 
                  ? 'bg-kkl-green text-white font-bold shadow-md' 
                  : ''
                }
                ${day.isSelected && !day.isToday 
                  ? 'bg-kkl-green-light ring-2 ring-kkl-green' 
                  : ''
                }
                ${!day.isCurrentMonth ? 'opacity-30' : ''}
              `}
            >
              <span className={`
                text-sm font-medium
                ${day.isToday ? 'text-white' : 'text-gray-700'}
                ${!day.isCurrentMonth ? 'text-gray-400' : ''}
              `}>
                {day.date}
              </span>
              
              {/* Event dots */}
              {day.events.length > 0 && day.isCurrentMonth && (
                <div className="absolute bottom-1 left-1/2 -translate-x-1/2 flex gap-0.5">
                  {day.events.slice(0, 3).map((event, i) => (
                    <span 
                      key={i}
                      className={`w-1.5 h-1.5 rounded-full ${
                        day.isToday ? 'bg-white' : eventTypeColors[event.type]
                      }`}
                    />
                  ))}
                  {day.events.length > 3 && (
                    <span className="text-[8px] text-gray-500">+{day.events.length - 3}</span>
                  )}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Selected Day Events */}
      <div className="border-t border-gray-100 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Clock className="w-4 h-4 text-kkl-green" />
          {selectedDate ? (
            <>פעילויות ל-{selectedDate.getDate()} {hebrewMonths[selectedDate.getMonth()]}</>
          ) : (
            'בחר תאריך'
          )}
        </h3>
        
        {selectedDayEvents.length === 0 ? (
          <div className="bg-gray-50 rounded-xl p-4 text-center">
            <p className="text-gray-500 text-sm">אין פעילויות מתוכננות</p>
          </div>
        ) : (
          <div className="space-y-2">
            {selectedDayEvents.map((event) => (
              <button
                key={event.id}
                onClick={() => onEventClick?.(event)}
                className="w-full flex items-center gap-3 p-3 bg-gray-50 hover:bg-kkl-green-light rounded-xl transition-colors text-right"
              >
                <span className={`w-2 h-8 rounded-full ${eventTypeColors[event.type]}`} />
                <div className="flex-1">
                  <p className="font-medium text-gray-800 text-sm">{event.title}</p>
                  <p className="text-xs text-gray-500">{eventTypeLabels[event.type]}</p>
                </div>
                {event.status && (
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    event.status === 'approved' 
                      ? 'bg-green-100 text-green-700' 
                      : event.status === 'pending'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}>
                    {event.status === 'approved' ? 'אושר' : event.status === 'pending' ? 'ממתין' : 'הושלם'}
                  </span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="border-t border-gray-100 px-4 py-3 bg-gray-50">
        <div className="flex items-center justify-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-kkl-green" />
            הזמנות
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            דיווחים
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-purple-500" />
            פגישות
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            דדליינים
          </span>
        </div>
      </div>
    </div>
  );
};

export default ModernCalendar;

