using System;
using System.IO;
using System.Web.Script.Serialization;

public sealed class RewardData {
    public string date;
    public bool[] completed = new bool[3];
    public bool badge_claimed;
}

// Local, self-reported demo goals. Sensor readings never award points.
public sealed class Rewards {
    public static readonly string[] Goals = {"Daily check-in", "Personal care goal", "Rest & recharge"};
    readonly string path;
    RewardData data = new RewardData();
    public string Message = "Small steps, at your own pace.";
    public Rewards(string file = null) {
        path = file;
        if (path != null && File.Exists(path)) {
            try {
                RewardData loaded = new JavaScriptSerializer().Deserialize<RewardData>(File.ReadAllText(path));
                if (loaded != null && loaded.completed != null && loaded.completed.Length == 3) data = loaded;
            } catch { Message = "Starting a fresh rewards demo."; }
        }
        Refresh(DateTime.Today.ToString("yyyy-MM-dd"));
        if (Points < 60) data.badge_claimed = false;
    }
    public bool Refresh(string today) {
        if (data.date == today) return false;
        data = new RewardData { date = today };
        Message = "A fresh day. Start at your pace.";
        return true;
    }
    public int Points { get { int n=0; foreach (bool done in data.completed) if(done)n+=20; return n; } }
    public bool Claimed { get { return data.badge_claimed; } }
    public bool Done(int index) { return data.completed[index]; }
    public bool Complete(int index) {
        Refresh(DateTime.Today.ToString("yyyy-MM-dd"));
        if (index<0 || index>=3 || data.completed[index]) return false;
        data.completed[index] = true;
        Message = Points == 60 ? "Your Balance badge is ready!" : "+20 points. Your effort counts.";
        Save(); return true;
    }
    public bool Claim() {
        Refresh(DateTime.Today.ToString("yyyy-MM-dd"));
        if (Points < 60 || data.badge_claimed) return false;
        data.badge_claimed = true;
        Message = "Balance badge earned. Well done!";
        Save(); return true;
    }
    void Save() {
        if (path == null) return;
        try {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            string temporary = path + ".tmp";
            File.WriteAllText(temporary, new JavaScriptSerializer().Serialize(data));
            if(File.Exists(path)) File.Replace(temporary,path,null); else File.Move(temporary,path);
        } catch { Message = "Progress is available this session only."; }
    }
}
