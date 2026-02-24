-- תיקון טקסט עברי בטבלת areas
-- =====================================================

-- עדכון האזורים במרחב צפון
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

-- עדכון האזורים במרחב מרכז
UPDATE areas 
SET name = N'שפלה וחוף',
    description = N'שפלת יהודה, מישור החוף, גוש דן'
WHERE code = 'SHFELA_COAST';

UPDATE areas 
SET name = N'מנשה ושרון',
    description = N'רמת מנשה, השרון, עמק חפר'
WHERE code = 'MENASHE_SHARON';

UPDATE areas 
SET name = N'מנסרה מרכז',
    description = N'אזור מנסרה מרכז'
WHERE code = 'MENSARA_CENTER';

UPDATE areas 
SET name = N'ההר',
    description = N'הרי יהודה, הרי ירושלים, הרי השומרון'
WHERE code = 'HAHAR';

-- עדכון האזורים במרחב דרום
UPDATE areas 
SET name = N'נגב צפוני',
    description = N'נגב צפוני, באר שבע, ערד'
WHERE code = 'NEGEV_NORTH';

UPDATE areas 
SET name = N'נגב מערבי',
    description = N'נגב מערבי, רהט, אופקים'
WHERE code = 'NEGEV_WEST';

UPDATE areas 
SET name = N'הר הנגב וערבה',
    description = N'הר הנגב, הערבה, אילת'
WHERE code = 'HAR_NEGEV_ARAVA';

UPDATE areas 
SET name = N'שימור קרקע',
    description = N'יחידת שימור קרקע ארצית'
WHERE code = 'LAND_CONSERVATION';

-- עדכון הטבלה regions אם צריך
UPDATE regions 
SET name = N'מרחב צפון'
WHERE code = 'NORTH';

UPDATE regions 
SET name = N'מרחב מרכז'
WHERE code = 'CENTER';

UPDATE regions 
SET name = N'מרחב דרום'
WHERE code = 'SOUTH';

-- בדיקה שהעדכון עבד
SELECT 
    a.id,
    a.code,
    a.name,
    a.description,
    r.name as region_name
FROM areas a
JOIN regions r ON a.region_id = r.id
ORDER BY r.id, a.id;
