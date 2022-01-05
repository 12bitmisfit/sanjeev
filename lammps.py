import itertools as it
import concurrent.futures as cf

#simulation vars
number_of_type = 5
number_of_frames = 1000
lower_bound = 349.5
middle_bound = 390.5
upper_bound = 410.5



# Added before I knew what data I needed, didn't use these vars
atoms = 148026
radius = 46.2
cyl_length = 40
res_length = 350
bins = 100
xmax = 0
xmin = 46.2
pheight = 0.995
pore_center = [100.0, 100.0]


# Function to load the data from the lammpstrj dump
# It is setup to be multi threaded for faster loading of data
def frame(framescount, startline, endline):
    chunked_data = {"fc": [], "id": [], "mol": [], "type": [], "x": [], "y": [], "z": [], "ix": [], "iy": [], "iz": []}
    with open('dump-prod.lammpstrj', 'r') as infile:
        lines_gen = it.islice(infile, startline, endline)
        for lines in lines_gen:
            # Converts the lines var from a string into an array of strings
            lines = lines.split()
            # Adds the data into the chunked_data dictionary and converts strings into proper data types
            chunked_data["fc"].append(framescount)
            chunked_data["id"].append(int(lines[0]))
            chunked_data["mol"].append(int(lines[1]))
            chunked_data["type"].append(int(lines[2]))
            # X and Y had this math applied to them in Sanjeev's script, so I did it too but this data isn't used.
            chunked_data["x"].append(float(lines[3]) - pore_center[0])
            chunked_data["y"].append(float(lines[4]) - pore_center[1])
            chunked_data["z"].append(float(lines[5]))
            chunked_data["ix"].append(int(lines[6]))
            chunked_data["iy"].append(int(lines[7]))
            chunked_data["iz"].append(int(lines[8]))
    return chunked_data

# Required for multithreading
if __name__ == '__main__':
    # By default cf.ProcessPoolExecutor() runs as many threads as your pc has, you can limit it like so: cf.ProcessPoolExecutor(max_workers = 4)
    with cf.ProcessPoolExecutor() as executor:
        # frames is the dictionary in shared memory that all the threads return to
        frames = {}
        time_frames = list(range(number_of_frames))
        # Workers needs its own list since it converts the elements from ints to future objects
        workers = time_frames
        # Start the workers
        for i in workers:
            if i == 0:
                startline = 9
                endline = 148035
                workers[i] = executor.submit(frame, i, startline, endline)
            else:
                startline = startline + 148035
                endline = endline + 148035
                workers[i] = executor.submit(frame, i, startline, endline)
        # Return data from threaded workers (chunked_data to frames)
        for i in time_frames:
            frames[str(i)] = workers[i].result()

        count = 0
        type5s = {}
        # Filters down to just the type of atom we want and stores the id, z, and fc in a new dict
        for i, type in enumerate(frames["0"]["type"]):
            type5 = {"id": 0, "z": [], "fc": []}
            if type == number_of_type:
                type5["id"] = frames["0"]["id"][i]
                for e in time_frames:
                    type5["z"].append(frames[str(e)]["z"][i])
                    type5["fc"].append(frames[str(e)]["fc"][i])
            if type5["id"] > 0:
                type5s[str(count)] = type5
                count = count + 1
        end = len(type5s)
        type5f = {}
        count = 0
        for i in range(0, end, 1):
            # Filters out any of the atoms that didn't make it to 410.5 with a sanity check to make sure that duplicates aren't added
            if max(type5s[str(i)]["z"]) >= upper_bound and type5f.get(str(i)) == None:
                count = count + 1
                type5f[str(count)] = type5s[str(i)]
        end = len(type5f)
        type5p = {}
        # Removes atoms that start above 349.5 in the first frame
        for i in range(1, end):
            for fc, z in zip(type5f[str(i)]["fc"], type5f[str(i)]["z"]):
                if fc == 0 and lower_bound <= z:
                    del type5f[str(i)]
        end = len(type5f)
        c = 0
        for i in range(1, end):
            id = type5f[str(i)]["id"]
            type5p[str(i)] = {"id": id, "z": [0,0,0], "fc": [0,0,0], "p": [False, False, False]}
            # Test the atoms that made it thus far to see if they meet the stated conditions
            for fc, z in zip(type5f[str(i)]["fc"], type5f[str(i)]["z"]):
                if lower_bound <= z < middle_bound and type5p[str(i)]["p"][0] is False and fc > 0:
                    type5p[str(i)]["z"][0] = z
                    type5p[str(i)]["fc"][0] = fc
                    type5p[str(i)]["p"][0] = True
                    #print("ID: " + str(id) + " passed 349.5 at FC: " + str(fc) + " with a z of: " + str(z))
                if middle_bound <= z < upper_bound and type5p[str(i)]["p"][1] is False and fc > 0:
                    type5p[str(i)]["z"][1] = z
                    type5p[str(i)]["fc"][1] = fc
                    type5p[str(i)]["p"][1] = True
                    #print("ID: " + str(id) + " passed 390.5 at FC: " + str(fc) + " with a z of: " + str(z))
                if z >= upper_bound and type5p[str(i)]["p"][2] is False and fc > 0:
                    type5p[str(i)]["z"][2] = z
                    type5p[str(i)]["fc"][2] = fc
                    type5p[str(i)]["p"][2] = True
                    #print("ID: " + str(id) + " passed 410.5 at FC: " + str(fc) + " with a z of: " + str(z))
            # Display the information
            if type5p[str(i)]["p"] == [True, True, True]:
                #print(type5p[str(i)])
                print("Atom " +str(type5p[str(i)]["id"]) + " passed " + str(lower_bound) + " at FC: " + str(type5p[str(i)]["fc"][0]) + " with a Z of " + str(type5p[str(i)]["z"][0]))
                print("Atom " + str(type5p[str(i)]["id"]) + " passed " + str(middle_bound) + " at FC: " + str(type5p[str(i)]["fc"][1]) + " with a Z of " + str(type5p[str(i)]["z"][1]))
                print("Atom " + str(type5p[str(i)]["id"]) + " passed " + str(upper_bound) + " at FC: " + str(type5p[str(i)]["fc"][2]) + " with a Z of " + str(type5p[str(i)]["z"][2]))
                print("It Took atom " + str(type5p[str(i)]["id"]) + " " + str(type5p[str(i)]["fc"][1] - type5p[str(i)]["fc"][0]) + " frames to travel from " + str(lower_bound) + " to " + str(middle_bound))
                c = c + 1
        print("There were " + str(c) + " atoms that made the journey")
