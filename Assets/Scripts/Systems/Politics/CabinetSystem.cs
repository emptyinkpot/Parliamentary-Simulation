using System;
using System.Collections.Generic;
using ImperialStrategy.Politics;

/// <summary>
/// Manages the imperial cabinet: appointments, dismissals, and dissolution.
/// </summary>
public static class CabinetSystem
{
    public enum CabinetStatus
    {
        Active,
        Resigned,
        Dissolved
    }

    public enum AppointmentType
    {
        Imperial,
        PrimeMinister
    }

    public struct MinisterData
    {
        public string MemberId;
        public string Name;
        public CabinetPosition Position;
        public AppointmentType AppointedBy;
        public DateTime AppointedDate;
        public float AbilityScore; // 0-100, affects system efficiency
    }

    private static readonly Dictionary<CabinetPosition, MinisterData> _ministers = new();
    private static CabinetStatus _status = CabinetStatus.Dissolved;

    public static CabinetStatus Status => _status;
    public static IReadOnlyDictionary<CabinetPosition, MinisterData> Ministers => _ministers;

    public static void Reset()
    {
        _ministers.Clear();
        _status = CabinetStatus.Dissolved;
    }

    public static bool FormCabinet(string pmMemberId, string pmName, float pmAbility)
    {
        if (_status == CabinetStatus.Active) return false;

        _ministers.Clear();
        _status = CabinetStatus.Active;

        _ministers[CabinetPosition.PrimeMinister] = new MinisterData
        {
            MemberId = pmMemberId,
            Name = pmName,
            Position = CabinetPosition.PrimeMinister,
            AppointedBy = AppointmentType.Imperial,
            AppointedDate = DateTime.UtcNow,
            AbilityScore = Math.Clamp(pmAbility, 0f, 100f)
        };
        return true;
    }

    /// <summary>
    /// Appoints a minister. PM cannot be appointed this way; use FormCabinet.
    /// </summary>
    public static bool AppointMinister(CabinetPosition position, string memberId,
        string name, float ability, AppointmentType appointedBy)
    {
        if (_status != CabinetStatus.Active) return false;
        if (position == CabinetPosition.PrimeMinister) return false;
        if (_ministers.ContainsKey(position)) return false;

        _ministers[position] = new MinisterData
        {
            MemberId = memberId,
            Name = name,
            Position = position,
            AppointedBy = appointedBy,
            AppointedDate = DateTime.UtcNow,
            AbilityScore = Math.Clamp(ability, 0f, 100f)
        };
        return true;
    }

    /// <summary>
    /// Dismisses a minister. Dismissing the PM triggers full cabinet dissolution.
    /// </summary>
    public static bool DismissMinister(CabinetPosition position)
    {
        if (_status != CabinetStatus.Active) return false;
        if (!_ministers.ContainsKey(position)) return false;

        if (position == CabinetPosition.PrimeMinister)
        {
            DissolveCabinet();
            return true;
        }

        _ministers.Remove(position);
        return true;
    }

    /// <summary>
    /// Dissolves the entire cabinet (total resignation).
    /// </summary>
    public static void DissolveCabinet()
    {
        _ministers.Clear();
        _status = CabinetStatus.Dissolved;
    }

    /// <summary>
    /// Returns all positions that have no minister assigned (excluding PM).
    /// </summary>
    public static List<CabinetPosition> GetVacantPositions()
    {
        var vacant = new List<CabinetPosition>();
        foreach (CabinetPosition pos in Enum.GetValues(typeof(CabinetPosition)))
        {
            if (pos == CabinetPosition.PrimeMinister) continue;
            if (!_ministers.ContainsKey(pos))
                vacant.Add(pos);
        }
        return vacant;
    }

    /// <summary>
    /// Returns average ability score of all serving ministers (0-100).
    /// Used as efficiency multiplier for government actions.
    /// </summary>
    public static float GetCabinetEfficiency()
    {
        if (_ministers.Count == 0) return 0f;
        float sum = 0f;
        foreach (var m in _ministers.Values)
            sum += m.AbilityScore;
        return sum / _ministers.Count;
    }
}
