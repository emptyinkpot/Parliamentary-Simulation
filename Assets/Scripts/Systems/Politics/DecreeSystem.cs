using System;
using System.Collections.Generic;
using ImperialStrategy.Politics;

/// <summary>
/// Manages imperial decrees: issuance, lifecycle, and emergency powers.
/// Only the Emperor can issue decrees.
/// </summary>
public static class DecreeSystem
{
    public const int DefaultDurationDays = 30;
    public const int EmergencyDurationDays = 7;

    public struct DecreeData
    {
        public string Id;
        public string Title;
        public string Content;
        public DecreeType Type;
        public DecreeStatus Status;
        public string IssuerId;
        public int Priority;
        public DateTime IssuedDate;
        public DateTime? ExpiryDate;
    }

    private static readonly Dictionary<string, DecreeData> _decrees = new();
    private static bool _parliamentSuspended;

    public static bool IsParliamentSuspended => _parliamentSuspended;

    public static void Reset()
    {
        _decrees.Clear();
        _parliamentSuspended = false;
    }

    public static IReadOnlyDictionary<string, DecreeData> AllDecrees => _decrees;

    public static DecreeData? GetDecree(string id)
    {
        return _decrees.TryGetValue(id, out var d) ? d : null;
    }

    /// <summary>
    /// Issues a new decree. Only the Emperor (issuerId) may call this.
    /// Duration 0 means permanent. Emergency decrees default to 7 days.
    /// </summary>
    public static DecreeData? IssueDecree(string id, string title, string content,
        DecreeType type, string issuerId, int priority, int durationDays = -1)
    {
        if (string.IsNullOrEmpty(title) || string.IsNullOrEmpty(content)) return null;
        priority = Math.Clamp(priority, 1, 10);

        if (durationDays < 0)
            durationDays = type == DecreeType.Emergency ? EmergencyDurationDays : DefaultDurationDays;

        var now = DateTime.UtcNow;
        var decree = new DecreeData
        {
            Id = id,
            Title = title,
            Content = content,
            Type = type,
            Status = DecreeStatus.Draft,
            IssuerId = issuerId,
            Priority = priority,
            IssuedDate = now,
            ExpiryDate = durationDays > 0 ? now.AddDays(durationDays) : null
        };

        _decrees[id] = decree;
        return decree;
    }

    /// <summary>
    /// Activates a draft decree. Emergency decrees with critical priority suspend parliament.
    /// </summary>
    public static bool Activate(string decreeId)
    {
        if (!_decrees.TryGetValue(decreeId, out var decree)) return false;
        if (decree.Status != DecreeStatus.Draft) return false;

        decree.Status = DecreeStatus.Active;
        _decrees[decreeId] = decree;

        if (decree.Type == DecreeType.Emergency && decree.Priority >= 8)
            _parliamentSuspended = true;

        return true;
    }

    /// <summary>
    /// Revokes an active decree. If it was suspending parliament, lifts the suspension.
    /// </summary>
    public static bool Revoke(string decreeId)
    {
        if (!_decrees.TryGetValue(decreeId, out var decree)) return false;
        if (decree.Status != DecreeStatus.Active) return false;

        decree.Status = DecreeStatus.Revoked;
        _decrees[decreeId] = decree;

        if (decree.Type == DecreeType.Emergency)
            RecalculateParliamentSuspension();

        return true;
    }

    /// <summary>
    /// Checks all active decrees for expiry based on current time.
    /// </summary>
    public static void TickExpiry()
    {
        var now = DateTime.UtcNow;
        var keys = new List<string>(_decrees.Keys);

        foreach (var key in keys)
        {
            var d = _decrees[key];
            if (d.Status == DecreeStatus.Active && d.ExpiryDate.HasValue && now >= d.ExpiryDate.Value)
            {
                d.Status = DecreeStatus.Expired;
                _decrees[key] = d;
            }
        }
        RecalculateParliamentSuspension();
    }

    private static void RecalculateParliamentSuspension()
    {
        _parliamentSuspended = false;
        foreach (var d in _decrees.Values)
        {
            if (d.Type == DecreeType.Emergency && d.Status == DecreeStatus.Active && d.Priority >= 8)
            {
                _parliamentSuspended = true;
                break;
            }
        }
    }
}
