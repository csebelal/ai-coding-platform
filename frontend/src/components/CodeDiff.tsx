'use client';

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged' | 'header';
  content: string;
  oldLineNum?: number;
  newLineNum?: number;
}

interface CodeDiffProps {
  oldCode?: string;
  newCode?: string;
  fileName?: string;
}

function parseDiff(oldCode: string, newCode: string): DiffLine[] {
  const oldLines = oldCode.split('\n');
  const newLines = newCode.split('\n');
  const result: DiffLine[] = [];

  // Simple line-by-line diff
  const maxLen = Math.max(oldLines.length, newLines.length);
  let oldIdx = 0;
  let newIdx = 0;

  while (oldIdx < oldLines.length || newIdx < newLines.length) {
    if (oldIdx >= oldLines.length) {
      // Only new lines remaining
      result.push({ type: 'added', content: newLines[newIdx], newLineNum: newIdx + 1 });
      newIdx++;
    } else if (newIdx >= newLines.length) {
      // Only old lines remaining
      result.push({ type: 'removed', content: oldLines[oldIdx], oldLineNum: oldIdx + 1 });
      oldIdx++;
    } else if (oldLines[oldIdx] === newLines[newIdx]) {
      // Same line
      result.push({ type: 'unchanged', content: oldLines[oldIdx], oldLineNum: oldIdx + 1, newLineNum: newIdx + 1 });
      oldIdx++;
      newIdx++;
    } else {
      // Different lines - look ahead to find matches
      let foundInNew = -1;
      let foundInOld = -1;
      
      for (let i = newIdx + 1; i < Math.min(newIdx + 10, newLines.length); i++) {
        if (newLines[i] === oldLines[oldIdx]) {
          foundInNew = i;
          break;
        }
      }
      
      for (let i = oldIdx + 1; i < Math.min(oldIdx + 10, oldLines.length); i++) {
        if (oldLines[i] === newLines[newIdx]) {
          foundInOld = i;
          break;
        }
      }
      
      if (foundInNew >= 0 && (foundInOld < 0 || foundInNew - newIdx <= foundInOld - oldIdx)) {
        // Lines were added before the match
        while (newIdx < foundInNew) {
          result.push({ type: 'added', content: newLines[newIdx], newLineNum: newIdx + 1 });
          newIdx++;
        }
      } else if (foundInOld >= 0) {
        // Lines were removed before the match
        while (oldIdx < foundInOld) {
          result.push({ type: 'removed', content: oldLines[oldIdx], oldLineNum: oldIdx + 1 });
          oldIdx++;
        }
      } else {
        // Both changed
        result.push({ type: 'removed', content: oldLines[oldIdx], oldLineNum: oldIdx + 1 });
        result.push({ type: 'added', content: newLines[newIdx], newLineNum: newIdx + 1 });
        oldIdx++;
        newIdx++;
      }
    }
  }

  return result;
}

export function CodeDiff({ oldCode = '', newCode = '', fileName }: CodeDiffProps) {
  const lines = parseDiff(oldCode, newCode);
  const added = lines.filter(l => l.type === 'added').length;
  const removed = lines.filter(l => l.type === 'removed').length;

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {(fileName || (added > 0 || removed > 0)) && (
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {fileName && <span className="text-sm font-medium text-gray-900">{fileName}</span>}
          </div>
          <div className="text-sm space-x-3">
            {added > 0 && <span className="text-green-600">+{added} added</span>}
            {removed > 0 && <span className="text-red-600">-{removed} removed</span>}
          </div>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full font-mono text-sm">
          <tbody>
            {lines.map((line, i) => (
              <tr
                key={i}
                className={
                  line.type === 'added' ? 'bg-green-50' :
                  line.type === 'removed' ? 'bg-red-50' :
                  ''
                }
              >
                <td className="w-12 px-2 py-0.5 text-right text-gray-400 select-none border-r border-gray-200">
                  {line.oldLineNum || ''}
                </td>
                <td className="w-12 px-2 py-0.5 text-right text-gray-400 select-none border-r border-gray-200">
                  {line.newLineNum || ''}
                </td>
                <td className="w-8 px-2 py-0.5 text-center select-none">
                  {line.type === 'added' && <span className="text-green-600">+</span>}
                  {line.type === 'removed' && <span className="text-red-600">-</span>}
                </td>
                <td className="px-2 py-0.5 whitespace-pre">{line.content}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
