import React from 'react';
import ActivityLogNew from './ActivityLogNew';

/** יומן פעילות למנהלת חשבונות — פעילויות כספיות בלבד */
const AccountantActivityLog: React.FC = () => <ActivityLogNew mode="accountant" />;

export default AccountantActivityLog;
