using System;
using System.Collections.Generic;
using ImperialStrategy.Politics;

/// <summary>
/// Manages political parties: creation, dissolution, spectrum, and coalitions.
/// </summary>
public static class PartySystem
{
    public const int RequiredSupporters = 15;
    public const int FormingDurationDays = 7;
    public const int NameMinLength = 2;
    public const int NameMaxLength = 20;
    public const int ManifestoMinLength = 50;
    public const int ManifestoMaxLength = 500;
    public const int MaxTags = 5;

    public struct PoliticalSpectrum
    {
        public int Economic;      // 0 planned - 100 market
        public int Political;     // 0 democratic - 100 authoritarian
        public int Social;        // 0 liberal - 100 conservative
        public int International; // 0 internationalist - 100 nationalist
    }

    public struct PartyData
    {
        public string Id;
        public string Name;
        public string Abbreviation;
        public string Manifesto;
        public string FounderId;
        public string LeaderId;
        public PoliticalSpectrum Spectrum;
        public bool IsEstablished;
        public DateTime CreatedDate;
        public DateTime ExpiryDate;
        public List<string> MemberIds;
        public List<string> SupporterIds;
        public List<string> Tags;
    }

    private static readonly Dictionary<string, PartyData> _parties = new();
    private static readonly Dictionary<string, string> _memberParty = new();
    private static readonly List<CoalitionData> _coalitions = new();

    public struct CoalitionData
    {
        public string Id;
        public string Name;
        public string LeaderPartyId;
        public List<string> MemberPartyIds;
    }

    public static void Reset()
    {
        _parties.Clear();
        _memberParty.Clear();
        _coalitions.Clear();
    }

    public static PartyData? GetParty(string partyId)
    {
        return _parties.TryGetValue(partyId, out var p) ? p : null;
    }

    public static string GetMemberParty(string memberId)
    {
        return _memberParty.TryGetValue(memberId, out var pid) ? pid : null;
    }

    /// <summary>
    /// Creates a party in forming state. Must gather 15 supporters within 7 days.
    /// </summary>
    public static PartyData? CreateParty(string id, string name, string abbreviation,
        string manifesto, string founderId, PoliticalSpectrum spectrum, List<string> tags)
    {
        if (name.Length < NameMinLength || name.Length > NameMaxLength) return null;
        if (manifesto.Length < ManifestoMinLength || manifesto.Length > ManifestoMaxLength) return null;
        if (tags != null && tags.Count > MaxTags) return null;
        if (_memberParty.ContainsKey(founderId)) return null;

        var now = DateTime.UtcNow;
        var party = new PartyData
        {
            Id = id,
            Name = name,
            Abbreviation = abbreviation,
            Manifesto = manifesto,
            FounderId = founderId,
            LeaderId = founderId,
            Spectrum = spectrum,
            IsEstablished = false,
            CreatedDate = now,
            ExpiryDate = now.AddDays(FormingDurationDays),
            MemberIds = new List<string> { founderId },
            SupporterIds = new List<string> { founderId },
            Tags = tags ?? new List<string>()
        };

        _parties[id] = party;
        _memberParty[founderId] = id;
        return party;
    }

    /// <summary>
    /// Adds a supporter. If threshold reached, party becomes established.
    /// </summary>
    public static bool AddSupporter(string partyId, string supporterId)
    {
        if (!_parties.TryGetValue(partyId, out var party)) return false;
        if (party.IsEstablished) return false;
        if (DateTime.UtcNow > party.ExpiryDate) return false;
        if (party.SupporterIds.Contains(supporterId)) return false;

        party.SupporterIds.Add(supporterId);

        if (party.SupporterIds.Count >= RequiredSupporters)
        {
            party.IsEstablished = true;
        }

        _parties[partyId] = party;
        return true;
    }

    public static bool JoinParty(string partyId, string memberId)
    {
        if (!_parties.TryGetValue(partyId, out var party)) return false;
        if (!party.IsEstablished) return false;
        if (_memberParty.ContainsKey(memberId)) return false;

        party.MemberIds.Add(memberId);
        _parties[partyId] = party;
        _memberParty[memberId] = partyId;
        return true;
    }

    public static bool DissolveParty(string partyId)
    {
        if (!_parties.TryGetValue(partyId, out var party)) return false;

        foreach (var mid in party.MemberIds)
            _memberParty.Remove(mid);

        _parties.Remove(partyId);
        _coalitions.RemoveAll(c => c.MemberPartyIds.Contains(partyId));
        return true;
    }

    public static bool ElectLeader(string partyId, string newLeaderId)
    {
        if (!_parties.TryGetValue(partyId, out var party)) return false;
        if (!party.MemberIds.Contains(newLeaderId)) return false;

        party.LeaderId = newLeaderId;
        _parties[partyId] = party;
        return true;
    }

    public static CoalitionData? CreateCoalition(string id, string name, string leaderPartyId)
    {
        if (!_parties.ContainsKey(leaderPartyId)) return null;

        var coalition = new CoalitionData
        {
            Id = id,
            Name = name,
            LeaderPartyId = leaderPartyId,
            MemberPartyIds = new List<string> { leaderPartyId }
        };
        _coalitions.Add(coalition);
        return coalition;
    }

    public static bool JoinCoalition(string coalitionId, string partyId)
    {
        if (!_parties.ContainsKey(partyId)) return false;
        var idx = _coalitions.FindIndex(c => c.Id == coalitionId);
        if (idx < 0) return false;

        var coal = _coalitions[idx];
        if (coal.MemberPartyIds.Contains(partyId)) return false;
        coal.MemberPartyIds.Add(partyId);
        _coalitions[idx] = coal;
        return true;
    }

    public static string GetEconomicLabel(int value)
    {
        if (value <= 20) return "计划经济派";
        if (value <= 40) return "左翼经济";
        if (value <= 60) return "中间派";
        if (value <= 80) return "右翼经济";
        return "自由市场派";
    }

    public static string GetPoliticalLabel(int value)
    {
        if (value <= 20) return "民主主义者";
        if (value <= 40) return "温和民主";
        if (value <= 60) return "中间派";
        if (value <= 80) return "威权主义";
        return "绝对权威";
    }

    public static string GetSocialLabel(int value)
    {
        if (value <= 20) return "激进自由派";
        if (value <= 40) return "自由派";
        if (value <= 60) return "温和派";
        if (value <= 80) return "保守派";
        return "传统主义者";
    }

    public static string GetInternationalLabel(int value)
    {
        if (value <= 20) return "国际主义者";
        if (value <= 40) return "亲国际派";
        if (value <= 60) return "中立派";
        if (value <= 80) return "民族主义者";
        return "极端民族主义";
    }
}
