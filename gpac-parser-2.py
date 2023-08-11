import sys
import math
from plotter import Plotter

class Log:
    """
    Class Log which holds all information related to a single log
    """
    def __init__(self, line, type="DASH"):
        self.type=type
        self.video=0
        self.audio=0
        self.bitrate_switch=0
        self.width=0
        self.height=0
        self.data=0
        self.time=0
        self.segment_size=0
        self.throughput=0
        self.bitrate_level=0
        self.sample_rate=0
        self.bitrate=0
        self.buffer=0
        self.start_up_latency=0
        self.current_buffer=0
        self.buffer_threshold=0
        self.__extract_info(line)
        width=0
        height=0
        sample_rate=0

    def __extract_info(self, line):
        if(self.type=="DASH"):
            self.__extract_info_dash(line)
        elif(self.type=="HTTP"):
            self.__extract_info_http(line)
        elif(self.type=="BUFFER"):
            self.__extract_info_buffer(line)

    def __extract_info_buffer(self, line):
        words=list(line.split())
        self.current_buffer=int(words[2])
        self.buffer_threshold=int(words[4])

    def __extract_info_http(self, line):
        words=list(line.split())
        self.start_up_latency=float(words[10][1:])/1000

    def __extract_info_dash(self, line):
        words=list(line.split())
        for i in range(0, len(words)):
            if(words[i]==b'AS#1'):
                # Assuming AS1 is Adaptation set of videos
                self.video=1
            elif(words[i]==b'AS#2'):
                # Assuming AS2 is Adaptation set for audio
                self.audio=1
            elif(words[i]==b'changed' and words[i+1]==b'quality'):
                self.bitrate_switch=1
                self.__set_bitrate_switch(line)
                break
            elif(words[i]==b'got'):
                self.__set_current_status(line)
                break

    def __set_bitrate_switch(self, line):
        words=list(line.split())
        if(self.video):
            # Setting Video bitrate switching parameters
            self.bitrate_level=int(words[6])
            self.width=int(words[10])
            self.height=int(words[12])
            Log.width=self.width
            Log.height=self.height
        elif(self.audio):
            # Setting Audio bitrate switching parameters
            self.bitrate_level=int(words[6])
            self.sample_rate=int(words[11])
            Log.sample_rate=self.sample_rate

    def __set_current_status(self, line):
        words=list(line.split())
        self.data=int(words[5])
        self.time=float(words[8])
        self.throughput=float(words[11])
        self.segment_size=float(words[15])
        self.bitrate=float(words[19])
        self.bitrate_level=int(words[21][:len(words[21])-1])
        self.buffer=int(words[25])
        if(self.video):
            self.width=Log.width
            self.height=Log.height
        elif(self.audio):
            self.sample_rate=Log.sample_rate

    def __str__(self):
        ds=[]
        ds.append(("Type", self.type))
        ds.append(("Audio", self.audio))
        ds.append(("Video", self.video))
        ds.append(("Bitrate-switch", self.bitrate_switch))
        ds.append(("Width", self.width))
        ds.append(("Height", self.height))
        ds.append(("Sample-Rate", self.sample_rate))
        ds.append(("Data", self.data))
        ds.append(("Time", self.time))
        ds.append(("Segment size", self.segment_size))
        ds.append(("Throughput", self.throughput))
        ds.append(("Bitrate-level", self.bitrate_level))
        ds.append(("Bitrate", self.bitrate))
        ds.append(("Buffer", self.buffer))
        ds.append(("Start Up Latency", self.start_up_latency))
        ds.append(("Current buffer ", self.current_buffer))
        ds.append(("Buffer threshold ", self.buffer_threshold))
        return " "+str(ds)



class Logs:
    """
    Class Logs holds a set of DASH audio and video logs and its statistics
    """
    def __init__(self):
        self.config={"AUDIO_LOGGING":True, "VIDEO_LOGGING":True, "HTTP_LOGGING":True, "BUFFER_LOGGING": True}
        self.audio_logs=[]
        self.video_logs=[]
        self.http_logs=[]
        self.buffer_logs=[]
        self.audio_info={
                            'bitrate_switches': 0,
                            'average_bitrate': 0,
                            'average_throughput': 0,
                            'average_buffer': 0,
                            'average_rtt': 0,
                            'jitter': 0,
                            'throughput_sd' : 0,
                            'throughput_deviation': 0
                        }
        self.video_info={
                            'playback_time': 0,
                            'bitrate_switches': 0,
                            'average_bitrate': 0,
                            'average_throughput': 0,
                            'average_buffer': 0,
                            'average_rtt': 0,
                            'jitter': 0,
                            'throughput_sd': 0,
                            'throughput_deviation': 0
                        }
        self.total_throughput=0
        self.total_buffer=0
        self.buffer_info={
                            'number_of_interruptions': 0,
                            'time_under_interruptions': 0
                         }

    def configure(self, key, value):
        if(key in self.config.keys()):
            self.config[key]=value
        else:
            print("Trying to set an unknown configuration!!")

    def parse_logs(self, file_lines, scriptRunnerlog):
        lines=[]
        for f_line in file_lines:
            lines.extend(f_line.splitlines())
        # Create the logs and put them in respective lists
        for line in lines:
            words=list(line.split())
            # For processing DASH logs
            if(len(words)>1 and words[0]==b'[DASH]' and (words[1]==b'AS#1' or words[1]==b'AS#2') and (words[4]!=b'done')):
                log=Log(line, "DASH")
                if(log.audio and self.config["AUDIO_LOGGING"]):
                    self.audio_logs.append(log)
                if(log.video and self.config["VIDEO_LOGGING"]):
                    self.video_logs.append(log)
            # For processing HTTP logs
            elif(len(words)>4 and words[0]==b'[HTTP]' and words[4]==b'downloaded' and self.config["HTTP_LOGGING"]):
                log=Log(line, "HTTP")
                self.http_logs.append(log)
            elif(len(words)>2 and words[0]==b'[VideoOut]' and words[1]==b'buffer' and self.config["BUFFER_LOGGING"]):
                log=Log(line, "BUFFER")
                self.buffer_logs.append(log)
        # Get stats from logs if AUDIO_LOG
        if(self.config["AUDIO_LOGGING"]):
            counter=0
            prev_time=-1
            prev_throughput=-1
            for log in self.audio_logs:
                if(log.bitrate_switch):
                    self.audio_info['bitrate_switches']+=1
                else:
                    counter+=1
                    self.audio_info['average_bitrate']+=log.bitrate
                    self.audio_info['average_throughput']+=log.throughput
                    self.audio_info['average_buffer']+=log.buffer
                    self.audio_info['average_rtt']+=log.time
                    if(prev_time!=-1 and prev_throughput!=-1):
                        self.audio_info['jitter']+=abs(log.time-prev_time)
                        self.audio_info['throughput_deviation']+=abs(log.throughput-prev_throughput)
                    prev_time=log.time
                    prev_throughput=log.throughput
            self.audio_info['average_bitrate']/= max(1,counter)
            self.audio_info['average_throughput']/=max(1,counter)
            self.audio_info['average_buffer']/=max(1,counter)
            self.audio_info['average_rtt']/=max(1,counter)
            self.audio_info['jitter']/=max(1,counter-1)
            self.audio_info['throughput_deviation']/=max(1,counter-1)
            for log in self.audio_logs:
                self.audio_info['throughput_sd']+=(log.throughput-self.audio_info['average_throughput'])**2
            self.audio_info['throughput_sd']/=max(1,counter)
            self.audio_info['throughput_sd']=math.sqrt(self.audio_info['throughput_sd'])
        # Get stats from logs if VIDEO_LOG
        if(self.config["VIDEO_LOGGING"]):
            counter=0
            prev_time=-1
            prev_throughput=-1
            for log in self.video_logs:
                if(log.bitrate_switch):
                    self.video_info['bitrate_switches']+=1
                else:
                    counter+=1
                    self.video_info['playback_time']+=log.segment_size*1000
                    self.video_info['average_bitrate']+=log.bitrate
                    self.video_info['average_throughput']+=log.throughput
                    self.video_info['average_buffer']+=log.buffer
                    self.video_info['average_rtt']+=log.time
                    if(prev_time!=-1 and prev_throughput!=-1):
                        self.video_info['jitter']+=abs(log.time-prev_time)
                        self.video_info['throughput_deviation']+=abs(log.throughput-prev_throughput)
                    prev_time=log.time
                    prev_throughput=log.throughput
            self.video_info['average_bitrate']/=counter
            self.video_info['average_throughput']/=counter
            self.video_info['average_buffer']/=counter
            self.video_info['average_rtt']/=counter
            self.video_info['jitter']/=(counter-1)
            self.video_info['throughput_deviation']/=(counter-1)
            for log in self.video_logs:
                self.video_info['throughput_sd']+=(log.throughput-self.video_info['average_throughput'])**2
            self.video_info['throughput_sd']/=counter
            self.video_info['throughput_sd']=math.sqrt(self.video_info['throughput_sd'])
        self.total_throughput=self.audio_info['average_throughput']+self.video_info['average_throughput']
        self.total_buffer=self.audio_info['average_buffer']+self.video_info['average_buffer']
        # Get stats from logs if BUFFER_LOGGING
        if(self.config['BUFFER_LOGGING']):
            num_of_time_buffer_low=0
            num_of_time_buffer_high=0
            flag=0
            for log in self.buffer_logs:
                if(log.current_buffer<log.buffer_threshold):
                    num_of_time_buffer_low+=1
                    if(flag==0):
                        self.buffer_info['number_of_interruptions']+=1
                        flag=1
                else:
                    num_of_time_buffer_high+=1
                    flag=0
            total_duration=0
            s_f=open(scriptRunnerlog, "r")
            s_f_lines=s_f.readlines()
            for line in s_f_lines:
                if(line.find("gpac")!=-1):
                    total_duration=float(line.split("@time@")[1].strip())
            self.buffer_info['time_under_interruptions']=(total_duration*1000-self.video_info['playback_time'])

    def print_info(self):
        if(self.config["AUDIO_LOGGING"]):
            print("Audio Stream Information - ")
            print("----------------------------")
            print("Num of Bitrate switches: ", self.audio_info['bitrate_switches'])
            print("Average Bitrate: ", self.audio_info['average_bitrate'], "kbps")
            print("Average Throughput: ", self.audio_info['average_throughput'], "kbps")
            print("Average Buffer: ", self.audio_info['average_buffer'], "ms")
            print("Average RTT: ", self.audio_info['average_rtt'], "s")
            print("Throughput SD: ", self.audio_info['throughput_sd'])
            print("Throughput Deviation: ", self.audio_info['throughput_deviation'])
            print("Jitter: ", self.audio_info['jitter']*1000, "ms")
            print()
        if(self.config["VIDEO_LOGGING"]):
            print("Video Stream Information - ")
            print("----------------------------")
            print("Total Playback time: ", self.video_info['playback_time']/1000, "s")
            print("Num of Bitrate switches: ", self.video_info['bitrate_switches'])
            print("Average Bitrate: ", self.video_info['average_bitrate'], "kbps")
            print("Average Throughput: ", self.video_info['average_throughput'], "kbps")
            print("Average Buffer: ", self.video_info['average_buffer'], "ms")
            print("Average RTT: ", self.video_info['average_rtt'], "s")
            print("Throughput SD: ", self.video_info['throughput_sd'])
            print("Throughput Deviation: ", self.video_info['throughput_deviation'])
            print("Jitter: ", self.video_info['jitter']*1000, "ms")
            print()
        if(self.config["AUDIO_LOGGING"] and self.config["VIDEO_LOGGING"]):
            print("Overall - ")
            print("----------------------------")
            print("Total throughput: ", self.total_throughput, "kbps")
            print("Total buffer: ", self.total_buffer, "ms")
        if(self.config["HTTP_LOGGING"]):
            print("Start Up Latency 1: ", self.http_logs[0].start_up_latency, "ms")
            if(self.config["AUDIO_LOGGING"] and self.config["VIDEO_LOGGING"]):
                print("Start Up Latency 2: ", self.http_logs[1].start_up_latency, "ms")
        if(self.config["BUFFER_LOGGING"]):
            print("Number of Interruptions: ", self.buffer_info['number_of_interruptions'])
            print("Time under Interruptions: ", self.buffer_info['time_under_interruptions']/1000, "s")

    def generate_plots(self, type="video"):
        plotter=Plotter()
        plotter.set_point_type(0)
        if(self.config["AUDIO_LOGGING"]):
            self.__plot_audio_stats(plotter)
        if(self.config["VIDEO_LOGGING"]):
            self.__plot_video_stats(plotter)

    def __plot_video_stats(self, plotter):
        x_bitrate_level=[]
        y_bitrate_level=[]
        x_bitrate=[]
        y_bitrate=[]
        x_throughput=[]
        y_throughput=[]
        x_buffer=[]
        y_buffer=[]
        x_rtt=[]
        y_rtt=[]
        counter=0
        for log in self.video_logs:
            if(not log.bitrate_switch):
                x_bitrate_level.append(counter)
                x_bitrate.append(counter)
                x_throughput.append(counter)
                x_buffer.append(counter)
                x_rtt.append(counter)
                y_bitrate_level.append(log.bitrate_level)
                y_bitrate.append(log.bitrate)
                y_throughput.append(log.throughput)
                y_buffer.append(log.buffer)
                y_rtt.append(log.time)
                counter+=1
        plotter.plot_graph(x_bitrate_level, y_bitrate_level, title="Video Bitrate Level",
                            xlabel="Chunck Number",
                            ylabel="Bitrate Level (kbps)",
                            output_filename="video_bitrate_level.eps"
                        )
        plotter.plot_graph(x_bitrate, y_bitrate, title="Video Bitrate",
                            xlabel="Chunck Number",
                            ylabel="Bitrate (kbps)",
                            output_filename="video_bitrate.eps"
                        )
        plotter.plot_graph(x_throughput, y_throughput, title="Video Throughput",
                            xlabel="Chunck Number",
                            ylabel="Throughput (kbps)",
                            output_filename="video_throughput.eps"
                        )
        plotter.plot_graph(x_buffer, y_buffer, title="Video Buffer",
                            xlabel="Chunck Number",
                            ylabel="Buffer (ms)",
                            output_filename="video_buffer.eps"
                        )
        plotter.plot_graph(x_rtt, y_rtt, title="Video RTT",
                            xlabel="Chunk Number",
                            ylabel="RTT (s)",
                            output_filename="video_rtt.eps"
                        )

    def __plot_audio_stats(self, plotter):
        x_bitrate_level=[]
        y_bitrate_level=[]
        x_bitrate=[]
        y_bitrate=[]
        x_throughput=[]
        y_throughput=[]
        x_buffer=[]
        y_buffer=[]
        x_rtt=[]
        y_rtt=[]
        counter=1
        for log in self.audio_logs:
            if(not log.bitrate_switch):
                x_bitrate_level.append(counter)
                x_bitrate.append(counter)
                x_throughput.append(counter)
                x_buffer.append(counter)
                x_rtt.append(counter)
                y_bitrate_level.append(log.bitrate_level)
                y_bitrate.append(log.bitrate)
                y_throughput.append(log.throughput)
                y_buffer.append(log.buffer)
                y_rtt.append(log.time)
                counter+=1
        plotter.plot_graph(x_bitrate_level, y_bitrate_level, title="Audio Bitrate Level",
                            xlabel="Chunck Number",
                            ylabel="Bitrate Level (kbps)",
                            output_filename="audio_bitrate_level.eps"
                        )
        plotter.plot_graph(x_bitrate, y_bitrate, title="Audio Bitrate",
                            xlabel="Chunck Number",
                            ylabel="Bitrate (kbps)",
                            output_filename="audio_bitrate.eps"
                        )
        plotter.plot_graph(x_throughput, y_throughput, title="Audio Throughput",
                            xlabel="Chunck Number",
                            ylabel="Throughput (kbps)",
                            output_filename="audio_throughput.eps"
                        )
        plotter.plot_graph(x_buffer, y_buffer, title="Audio Buffer",
                            xlabel="Chunck Number",
                            ylabel="Buffer (ms)",
                            output_filename="audio_buffer.eps"
                        )
        plotter.plot_graph(x_rtt, y_rtt, title="Audio RTT",
                            xlabel="Chunk Number",
                            ylabel="RTT (s)",
                            output_filename="audio_rtt.eps"
                        )


if __name__=="__main__":
    file_name=""
    try:
        if(len(sys.argv)>2):
            file_name=sys.argv[1]
    except:
        print("Error!: input log ffile not provided")
        exit
    with open(sys.argv[1], "rb") as f:
        logs=Logs()
        logs.configure("VIDEO_LOGGING", True)
        logs.configure("AUDIO_LOGGING", True)
        logs.configure("HTTP_LOGGING", True)
        logs.configure("BUFFER_LOGGING", True)
        logs.parse_logs(f.readlines(), sys.argv[2])
        logs.print_info()
        logs.generate_plots()
