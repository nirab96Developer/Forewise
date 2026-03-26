import { useMemo } from "react";
import { getUserRole, normalizeRole, UserRole } from "../utils/permissions";

export function useRoleAccess() {
  return useMemo(() => {
    const role = normalizeRole(getUserRole());
    return {
      role,
      isAdmin: role === UserRole.ADMIN,
      isRegionManager: role === UserRole.REGION_MANAGER,
      isAreaManager: role === UserRole.AREA_MANAGER,
      isWorkManager: role === UserRole.WORK_MANAGER,
      isCoordinator: role === UserRole.ORDER_COORDINATOR,
      isAccountant: role === UserRole.ACCOUNTANT,

      canManageSystem: role === UserRole.ADMIN,
      canManageBudgets: [UserRole.ADMIN, UserRole.REGION_MANAGER].includes(role),
      canApproveWorklogs: [UserRole.ADMIN, UserRole.AREA_MANAGER, UserRole.ACCOUNTANT].includes(role),
      canApproveInvoices: [UserRole.ADMIN, UserRole.ACCOUNTANT].includes(role),
      canCreateWO: [UserRole.ADMIN, UserRole.AREA_MANAGER, UserRole.WORK_MANAGER].includes(role),
      canEditWO: [UserRole.ADMIN, UserRole.AREA_MANAGER, UserRole.WORK_MANAGER].includes(role),
      canDeleteWO: role === UserRole.ADMIN,
      canCreateProject: [UserRole.ADMIN, UserRole.AREA_MANAGER].includes(role),
      canManageSuppliers: role === UserRole.ADMIN,
      canManageEquipment: role === UserRole.ADMIN,
      canScanEquipment: [UserRole.ADMIN, UserRole.WORK_MANAGER].includes(role),
      canManageLocations: [UserRole.ADMIN, UserRole.AREA_MANAGER].includes(role),
      canManageAreas: [UserRole.ADMIN, UserRole.REGION_MANAGER].includes(role),
      canManageRegions: role === UserRole.ADMIN,
      canManageRotation: [UserRole.ADMIN, UserRole.ORDER_COORDINATOR].includes(role),
      canApproveBudgetTransfers: [UserRole.ADMIN, UserRole.REGION_MANAGER].includes(role),
    };
  }, []);
}
