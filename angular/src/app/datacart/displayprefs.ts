/**
 * This module defines values and styles used across components within the DataCartModule.  These 
 * are provided via a class of static functions.
 */
import { DownloadStatus } from './cartconstants';

let _label = {};
_label[DownloadStatus.DOWNLOADED]  = 'Downloaded';
_label[DownloadStatus.COMPLETED]   = 'Completed';
_label[DownloadStatus.DOWNLOADING] = 'Downloading';
_label[DownloadStatus.PENDING]     = 'Pending';
_label[DownloadStatus.CANCELED]    = 'Canceled';
_label[DownloadStatus.WARNING]     = 'Warning';
_label[DownloadStatus.FAILED]      = 'Failed';
_label[DownloadStatus.ERROR]       = 'Error';

let _iconcl = {};
_iconcl[DownloadStatus.DOWNLOADED]  = 'faa faa-check';
_iconcl[DownloadStatus.COMPLETED]   = 'faa faa-check';
_iconcl[DownloadStatus.DOWNLOADING] = 'faa faa-clock-o';
_iconcl[DownloadStatus.PENDING]     = 'faa faa-clock-o';
_iconcl[DownloadStatus.CANCELED]    = 'faa faa-remove';
_iconcl[DownloadStatus.WARNING]     = 'faa faa-warning';
_iconcl[DownloadStatus.FAILED]      = 'faa faa-warning';
_iconcl[DownloadStatus.ERROR]       = 'faa faa-warning';

let _color = {};
_color[DownloadStatus.DOWNLOADED]  = 'green';
_color[DownloadStatus.COMPLETED]   = 'green';
_color[DownloadStatus.DOWNLOADING] = '#00ace6';
_color[DownloadStatus.PENDING]     = '#00ace6';
_color[DownloadStatus.CANCELED]    = 'darkorange';
_color[DownloadStatus.WARNING]     = 'darkorange';
_color[DownloadStatus.FAILED]      = 'darkorange';
_color[DownloadStatus.ERROR]       = 'red';

export class DisplayPrefs {

    private static readonly _dlsLabel = _label;
    private static readonly _dlsIconClass = _iconcl;
    private static readonly _dlsColor = _color;

    /**
     * return the style class designations that select the icon to represent the download 
     * status for a file
     */
    public static getDownloadStatusIcon(downloadStatus: string) : string {
        if (! DisplayPrefs._dlsIconClass[downloadStatus])
            return '';
        return DisplayPrefs._dlsIconClass[downloadStatus];
    }

    /**
     * return the style class designation for selecting an icon to represent the download 
     * status for a file
     */
    public static getDownloadStatusLabel(downloadStatus: string) : string {
        if (! DisplayPrefs._dlsLabel[downloadStatus])
            return '';
        return DisplayPrefs._dlsLabel[downloadStatus];
    }

    /**
     * return the icon color to use to indicate the download status of a file or collection
     */
    public static getDownloadStatusColor(downloadStatus: string) : string {
        if (! DisplayPrefs._dlsColor[downloadStatus])
            return 'green';
        return DisplayPrefs._dlsColor[downloadStatus];
    }
}
