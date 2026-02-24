-- =========================================================
-- תיקון מלא של כל הטקסט בעברית בכל הטבלאות
-- =========================================================

-- 1. תיקון טבלת AREAS (כל 12 האזורים)
-- =========================================================

-- מרחב צפון
UPDATE areas 
SET name = N'גליל עליון ורמת הגולן',
    description = N'גליל עליון, רמת הגולן, אזור החולה'
WHERE code = 'GALIL_UPPER_GOLAN';

UPDATE areas 
SET name = N'גליל מערבי וכרמל',
    description = N'גליל מערבי, הר הכרמל, חוף הכרמל'
WHERE code = 'GALIL_WEST_CARMEL';

UPDATE areas 
SET name = N'גליל תחתון וגלבוע',
    description = N'גליל תחתון, הר הגלבוע, עמק יזרעאל'
WHERE code = 'GALIL_LOWER_GILBOA';

UPDATE areas 
SET name = N'עמק החולה',
    description = N'עמק החולה, אצבע הגליל, רמת הגולן הצפונית'
WHERE code = 'EMEK_HULA';

-- מרחב מרכז
UPDATE areas 
SET name = N'שפלה וחוף',
    description = N'שפלת יהודה, מישור החוף, גוש דן'
WHERE code = 'SHFELA_COAST';

UPDATE areas 
SET name = N'ההר',
    description = N'הרי יהודה, הרי ירושלים, הרי השומרון'
WHERE code = 'HAHAR';

UPDATE areas 
SET name = N'מנשה ושרון',
    description = N'רמת מנשה, השרון, עמק חפר'
WHERE code = 'MENASHE_SHARON';

UPDATE areas 
SET name = N'מנסרה מרכז',
    description = N'אזור מנסרה מרכז יער'
WHERE code = 'MENSARA_CENTER';

-- מרחב דרום
UPDATE areas 
SET name = N'נגב צפוני',
    description = N'נגב צפוני, באר שבע, ערד'
WHERE code = 'NEGEV_NORTH';

UPDATE areas 
SET name = N'נגב מערבי',
    description = N'נגב מערבי, אופקים, נתיבות'
WHERE code = 'NEGEV_WEST';

UPDATE areas 
SET name = N'הר הנגב וערבה',
    description = N'הר הנגב, הערבה, אילת'
WHERE code = 'HAR_NEGEV_ARAVA';

UPDATE areas 
SET name = N'שימור קרקע',
    description = N'יחידת שימור קרקע ארצית'
WHERE code = 'LAND_CONSERVATION';

-- =========================================================
-- 2. בדיקה שהכל תוקן
-- =========================================================

-- בדיקת טבלת areas
SELECT 
    'AREAS' as [Table],
    code as [Code],
    name as [Name],
    description as [Description],
    CASE 
        WHEN name LIKE '%?%' OR description LIKE '%?%' 
        THEN 'PROBLEM' 
        ELSE 'OK' 
    END as [Status]
FROM areas
ORDER BY code;

-- בדיקת טבלת regions (למקרה שצריך)
SELECT 
    'REGIONS' as [Table],
    code as [Code],
    name as [Name],
    CASE 
        WHEN name LIKE '%?%' 
        THEN 'PROBLEM' 
        ELSE 'OK' 
    END as [Status]
FROM regions
ORDER BY code;

-- בדיקת טבלת locations
SELECT TOP 10
    'LOCATIONS' as [Table],
    code as [Code],
    name as [Name],
    CASE 
        WHEN name LIKE '%?%' 
        THEN 'PROBLEM' 
        ELSE 'OK' 
    END as [Status]
FROM locations
WHERE name LIKE '%?%'
ORDER BY code;

-- סיכום
SELECT 
    'Summary' as [Report],
    (SELECT COUNT(*) FROM areas WHERE name LIKE '%?%' OR description LIKE '%?%') as [Areas_With_Problems],
    (SELECT COUNT(*) FROM regions WHERE name LIKE '%?%') as [Regions_With_Problems],
    (SELECT COUNT(*) FROM locations WHERE name LIKE '%?%') as [Locations_With_Problems],
    (SELECT COUNT(*) FROM projects WHERE name LIKE '%?%' OR description LIKE '%?%') as [Projects_With_Problems];
