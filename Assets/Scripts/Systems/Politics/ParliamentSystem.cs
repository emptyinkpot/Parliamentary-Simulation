using System.Collections.Generic;
using ImperialStrategy.Politics;

/// <summary>
/// Manages the bicameral parliament: Upper House (90 seats) and Lower House (435 seats).
/// Handles bill lifecycle and voting logic.
/// </summary>
public static class ParliamentSystem
{
    public const int UpperLifetimeSeats = 20;
    public const int UpperMeritoriousSeats = 40;
    public const int UpperImperialSeats = 30;
    public const int UpperTotalSeats = 90;
    public const int LowerTotalSeats = 435;
    public const float QuorumRatio = 0.5f;

    public struct VoteTally
    {
        public int Support;
        public int Oppose;
        public int Abstain;
        public int Total => Support + Oppose + Abstain;
        public bool HasQuorum(int totalSeats) => Total >= (int)(totalSeats * QuorumRatio);
        public bool Passed => Total > 0 && Support > Total * 0.5f;
    }

    public struct BillData
    {
        public string Id;
        public string Title;
        public string Content;
        public string ProposerId;
        public BillStatus Status;
    }

    private static readonly Dictionary<string, BillData> _bills = new();
    private static readonly Dictionary<string, Dictionary<string, VoteChoice>> _votes = new();
    private static readonly Dictionary<string, Chamber> _memberChambers = new();

    public static void Reset()
    {
        _bills.Clear();
        _votes.Clear();
        _memberChambers.Clear();
    }

    public static void RegisterMember(string memberId, Chamber chamber)
    {
        _memberChambers[memberId] = chamber;
    }

    public static BillData? GetBill(string billId)
    {
        return _bills.TryGetValue(billId, out var bill) ? bill : null;
    }

    public static BillData SubmitBill(string id, string title, string content, string proposerId)
    {
        var bill = new BillData
        {
            Id = id,
            Title = title,
            Content = content,
            ProposerId = proposerId,
            Status = BillStatus.Pending
        };
        _bills[id] = bill;
        return bill;
    }

    public static bool StartVote(string billId)
    {
        if (!_bills.TryGetValue(billId, out var bill)) return false;
        if (bill.Status != BillStatus.Pending) return false;

        bill.Status = BillStatus.Voting;
        _bills[billId] = bill;
        _votes[billId] = new Dictionary<string, VoteChoice>();
        return true;
    }

    public static bool CastVote(string billId, string memberId, VoteChoice choice)
    {
        if (!_bills.TryGetValue(billId, out var bill)) return false;
        if (bill.Status != BillStatus.Voting) return false;
        if (!_memberChambers.ContainsKey(memberId)) return false;

        if (!_votes.ContainsKey(billId))
            _votes[billId] = new Dictionary<string, VoteChoice>();

        _votes[billId][memberId] = choice;
        return true;
    }

    public static VoteTally GetChamberTally(string billId, Chamber chamber)
    {
        var tally = new VoteTally();
        if (!_votes.TryGetValue(billId, out var billVotes)) return tally;

        foreach (var kv in billVotes)
        {
            if (!_memberChambers.TryGetValue(kv.Key, out var mem)) continue;
            if (mem != chamber) continue;

            switch (kv.Value)
            {
                case VoteChoice.Support: tally.Support++; break;
                case VoteChoice.Oppose: tally.Oppose++; break;
                case VoteChoice.Abstain: tally.Abstain++; break;
            }
        }
        return tally;
    }

    /// <summary>
    /// Tallies votes for both chambers. Bill passes only if both chambers pass with quorum met.
    /// Updates bill status to Passed or Rejected.
    /// </summary>
    public static BillStatus TallyVotes(string billId)
    {
        if (!_bills.TryGetValue(billId, out var bill)) return BillStatus.Rejected;
        if (bill.Status != BillStatus.Voting) return bill.Status;

        var upper = GetChamberTally(billId, Chamber.Upper);
        var lower = GetChamberTally(billId, Chamber.Lower);

        bool upperQuorum = upper.HasQuorum(UpperTotalSeats);
        bool lowerQuorum = lower.HasQuorum(LowerTotalSeats);

        bool passed = upperQuorum && lowerQuorum && upper.Passed && lower.Passed;

        bill.Status = passed ? BillStatus.Passed : BillStatus.Rejected;
        _bills[billId] = bill;
        return bill.Status;
    }
}
