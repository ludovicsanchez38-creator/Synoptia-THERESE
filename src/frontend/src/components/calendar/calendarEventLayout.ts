import type { CalendarEvent } from '../../services/api';

export interface TimedEventLayout {
  top: number;
  height: number;
  leftPercent: number;
  widthPercent: number;
}

interface TimedEventGeometry extends TimedEventLayout {
  eventId: string;
  startMinutes: number;
  endMinutes: number;
  columnIndex: number;
  columnCount: number;
}

interface ColumnEvent {
  startMinutes: number;
  endMinutes: number;
}

interface EventWithPosition {
  event: CalendarEvent;
  top: number;
  height: number;
  startMinutes: number;
  endMinutes: number;
}

export function getTimedEventLayout(
  events: CalendarEvent[],
  startHour: number,
  endHour: number,
  hourHeightPx: number
): Record<string, TimedEventLayout> {
  const positionedEvents = events
    .map((event) => getPositionedEvent(event, startHour, endHour, hourHeightPx))
    .filter((event): event is EventWithPosition => event !== null)
    .sort((a, b) => {
      if (a.startMinutes !== b.startMinutes) {
        return a.startMinutes - b.startMinutes;
      }
      if (a.endMinutes !== b.endMinutes) {
        return a.endMinutes - b.endMinutes;
      }
      return a.event.id.localeCompare(b.event.id);
    });

  const layouts: Record<string, TimedEventLayout> = {};
  let currentGroup: EventWithPosition[] = [];
  let currentGroupMaxEnd = -1;

  for (const event of positionedEvents) {
    if (currentGroup.length === 0 || event.startMinutes < currentGroupMaxEnd) {
      currentGroup.push(event);
      currentGroupMaxEnd = Math.max(currentGroupMaxEnd, event.endMinutes);
      continue;
    }

    applyGroupLayout(currentGroup, layouts);
    currentGroup = [event];
    currentGroupMaxEnd = event.endMinutes;
  }

  if (currentGroup.length > 0) {
    applyGroupLayout(currentGroup, layouts);
  }

  return layouts;
}

function getPositionedEvent(
  event: CalendarEvent,
  startHour: number,
  endHour: number,
  hourHeightPx: number
): EventWithPosition | null {
  if (!event.start_datetime || !event.end_datetime) {
    return null;
  }

  const start = new Date(event.start_datetime);
  const end = new Date(event.end_datetime);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return null;
  }

  const startMinutes = start.getHours() * 60 + start.getMinutes();
  const endMinutes = end.getHours() * 60 + end.getMinutes();
  const gridStartMinutes = startHour * 60;
  const gridEndMinutes = endHour * 60;
  const clampedStart = Math.max(startMinutes, gridStartMinutes);
  const clampedEnd = Math.min(endMinutes, gridEndMinutes);

  if (clampedStart >= clampedEnd) {
    return null;
  }

  return {
    event,
    top: ((clampedStart - gridStartMinutes) / 60) * hourHeightPx,
    height: ((clampedEnd - clampedStart) / 60) * hourHeightPx,
    startMinutes: clampedStart,
    endMinutes: clampedEnd,
  };
}

function applyGroupLayout(
  group: EventWithPosition[],
  layouts: Record<string, TimedEventLayout>
) {
  const columns: ColumnEvent[][] = [];
  const geometries: TimedEventGeometry[] = [];

  for (const item of group) {
    let columnIndex = columns.findIndex((column) =>
      column.every((placed) => !eventsOverlap(item.startMinutes, item.endMinutes, placed.startMinutes, placed.endMinutes))
    );

    if (columnIndex === -1) {
      columnIndex = columns.length;
      columns.push([]);
    }

    columns[columnIndex].push({
      startMinutes: item.startMinutes,
      endMinutes: item.endMinutes,
    });

    geometries.push({
      eventId: item.event.id,
      top: item.top,
      height: item.height,
      startMinutes: item.startMinutes,
      endMinutes: item.endMinutes,
      columnIndex,
      columnCount: 1,
      leftPercent: 0,
      widthPercent: 0,
    });
  }

  const totalColumns = Math.max(columns.length, 1);
  const columnWidth = 100 / totalColumns;

  for (const geometry of geometries) {
    let span = 1;
    for (let nextColumn = geometry.columnIndex + 1; nextColumn < totalColumns; nextColumn += 1) {
      const hasConflict = columns[nextColumn].some((placed) =>
        eventsOverlap(geometry.startMinutes, geometry.endMinutes, placed.startMinutes, placed.endMinutes)
      );
      if (hasConflict) {
        break;
      }
      span += 1;
    }

    geometry.columnCount = span;
    geometry.leftPercent = geometry.columnIndex * columnWidth;
    geometry.widthPercent = columnWidth * span;

    layouts[geometry.eventId] = {
      top: geometry.top,
      height: geometry.height,
      leftPercent: geometry.leftPercent,
      widthPercent: geometry.widthPercent,
    };
  }
}

function eventsOverlap(
  startA: number,
  endA: number,
  startB: number,
  endB: number
): boolean {
  return startA < endB && endA > startB;
}
